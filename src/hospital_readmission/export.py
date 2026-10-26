"""Export Utilities Module (FR-6, FR-11).

Provides functions to export cleaned datasets, analytical tables,
quality metrics, and pipeline logs in CSV and JSON formats.
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from hospital_readmission.logging_config import setup_logger

logger = setup_logger(__name__)


def export_dataframe_csv(
    df: pd.DataFrame,
    output_path: str | Path,
    index: bool = False,
) -> Path:
    """Exports a pandas DataFrame to CSV, ensuring parent directories exist."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index, encoding="utf-8")
    logger.info("Exported DataFrame to %s (%d rows)", path, len(df))
    return path


def export_metadata_json(
    metadata: dict[str, Any],
    output_path: str | Path,
) -> Path:
    """Exports pipeline run metadata or summary statistics to JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)
    logger.info("Exported metadata to %s", path)
    return path
