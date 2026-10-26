"""Data Ingestion Module (FR-1).

Loads CSV encounter records, performs file integrity checks,
handles encoding detection/fallbacks, and captures ingestion metadata.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from hospital_readmission.logging_config import setup_logger

logger = setup_logger(__name__)


@dataclass
class IngestionMetadata:
    """Metadata recorded during dataset ingestion."""

    source_path: str
    file_size_bytes: int
    row_count: int
    column_count: int
    columns: list[str]
    inferred_dtypes: dict[str, str]
    ingestion_timestamp: str
    encoding_used: str
    extra_info: dict[str, Any] = field(default_factory=dict)


class DataIngestionError(Exception):
    """Raised when data ingestion fails due to missing, invalid, or malformed files."""
    pass


class DatasetLoader:
    """Handles loading and initial inspection of healthcare encounter CSV files."""

    SUPPORTED_EXTENSIONS = {".csv", ".txt"}
    FALLBACK_ENCODINGS = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]

    def __init__(self, fallback_encodings: list[str] | None = None):
        if fallback_encodings:
            self.fallback_encodings = fallback_encodings
        else:
            self.fallback_encodings = self.FALLBACK_ENCODINGS

    def inspect_file(self, file_path: str | Path) -> dict[str, Any]:
        """Validates file existence, format, and size without loading all data into memory."""
        path = Path(file_path)

        if not path.exists():
            raise DataIngestionError(f"Dataset file does not exist: {path.resolve()}")

        if not path.is_file():
            raise DataIngestionError(f"Provided path is not a file: {path.resolve()}")

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise DataIngestionError(
                f"Unsupported file format '{path.suffix}'. "
                f"Supported formats: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )

        file_size = path.stat().st_size
        if file_size == 0:
            raise DataIngestionError(f"Dataset file is empty (0 bytes): {path.resolve()}")

        return {
            "path": str(path.resolve()),
            "file_name": path.name,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
        }

    def load_csv(
        self,
        file_path: str | Path,
        nrows: int | None = None,
        usecols: list[str] | None = None,
    ) -> tuple[pd.DataFrame, IngestionMetadata]:
        """Loads a CSV file into a Pandas DataFrame with automatic encoding fallback.

        Args:
            file_path: Path to the CSV file.
            nrows: Optional maximum rows to load (e.g. for previews or testing).
            usecols: Optional subset of columns to load.

        Returns:
            Tuple of (DataFrame, IngestionMetadata).

        Raises:
            DataIngestionError: If file cannot be read or is malformed.
        """
        file_info = self.inspect_file(file_path)
        path = Path(file_path)

        df: pd.DataFrame | None = None
        used_encoding: str | None = None
        last_error: Exception | None = None

        for encoding in self.fallback_encodings:
            try:
                logger.info("Attempting to load %s with encoding '%s'", path.name, encoding)
                df = pd.read_csv(
                    path,
                    encoding=encoding,
                    nrows=nrows,
                    usecols=usecols,
                    low_memory=False,
                )
                used_encoding = encoding
                break
            except (UnicodeDecodeError, UnicodeError) as e:
                logger.warning("Encoding '%s' failed for %s: %s", encoding, path.name, e)
                last_error = e
            except pd.errors.EmptyDataError as e:
                raise DataIngestionError(f"File contains no data or header: {path.name}") from e
            except pd.errors.ParserError as e:
                raise DataIngestionError(f"Malformed CSV content in {path.name}: {e}") from e
            except Exception as e:
                logger.error("Unexpected error reading %s: %s", path.name, e)
                last_error = e

        if df is None or used_encoding is None:
            raise DataIngestionError(
                f"Failed to read CSV '{path.name}' with any of the attempted encodings "
                f"({self.fallback_encodings}). Last error: {last_error}"
            )

        if df.empty:
            raise DataIngestionError(f"Loaded DataFrame from {path.name} is empty.")

        row_count = len(df)
        col_count = len(df.columns)
        columns = [str(c) for c in df.columns]
        inferred_dtypes = {str(col): str(dtype) for col, dtype in df.dtypes.items()}

        metadata = IngestionMetadata(
            source_path=str(path.resolve()),
            file_size_bytes=file_info["file_size_bytes"],
            row_count=row_count,
            column_count=col_count,
            columns=columns,
            inferred_dtypes=inferred_dtypes,
            ingestion_timestamp=datetime.now(UTC).isoformat(),
            encoding_used=used_encoding,
            extra_info={"preview_only": nrows is not None},
        )

        logger.info(
            "Successfully ingested '%s' (%d rows, %d columns, %.2f MB)",
            path.name,
            row_count,
            col_count,
            file_info["file_size_mb"],
        )

        return df, metadata


def load_id_mappings(mapping_file: str | Path) -> dict[str, dict[int, str]]:
    """Parses IDS_mapping.csv into separate lookup dictionaries.

    The UCI dataset IDS_mapping.csv contains 3 sections separated by empty lines:
    1. admission_type_id
    2. discharge_disposition_id
    3. admission_source_id

    Returns:
        Dict mapping section name to dict of id -> description.
    """
    path = Path(mapping_file)
    if not path.exists():
        logger.warning("Mapping file %s does not exist. IDs will remain unmapped.", path)
        return {}

    mappings: dict[str, dict[int, str]] = {
        "admission_type_id": {},
        "discharge_disposition_id": {},
        "admission_source_id": {},
    }

    current_section: str | None = None

    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue

                # Check if line introduces a new header
                if "admission_type_id" in line_str:
                    current_section = "admission_type_id"
                    continue
                elif "discharge_disposition_id" in line_str:
                    current_section = "discharge_disposition_id"
                    continue
                elif "admission_source_id" in line_str:
                    current_section = "admission_source_id"
                    continue

                if current_section and "," in line_str:
                    parts = line_str.split(",", 1)
                    raw_id = parts[0].strip()
                    desc = parts[1].strip() if len(parts) > 1 else ""
                    if raw_id.isdigit():
                        mappings[current_section][int(raw_id)] = desc
    except Exception as e:
        logger.error("Failed to parse ID mappings from %s: %s", path, e)

    return mappings
