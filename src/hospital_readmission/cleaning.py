"""Data Cleaning Module (FR-3).

Implements a configurable, auditable, and reproducible cleaning pipeline for
healthcare encounters, preserving raw data while documenting all transformations.
"""

import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd

from hospital_readmission.logging_config import setup_logger

logger = setup_logger(__name__)


@dataclass
class CleaningLogEntry:
    """Audit log entry for a discrete cleaning transformation."""

    timestamp: str
    operation: str
    target_column: str | None
    rows_before: int
    rows_after: int
    values_affected: int
    reason: str
    reversible: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CleaningPipeline:
    """Configurable pipeline for standardizing, validating, and cleaning encounter data."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        schema: dict[str, Any] | None = None,
        id_mappings: dict[str, dict[int, str]] | None = None,
    ):
        self.config = config or {}
        self.schema = schema or {}
        self.id_mappings = id_mappings or {}
        self.log_entries: list[CleaningLogEntry] = []

    def _log(
        self,
        operation: str,
        target_column: str | None,
        rows_before: int,
        rows_after: int,
        values_affected: int,
        reason: str,
        reversible: bool,
    ) -> None:
        entry = CleaningLogEntry(
            timestamp=datetime.now(UTC).isoformat(),
            operation=operation,
            target_column=target_column,
            rows_before=rows_before,
            rows_after=rows_after,
            values_affected=values_affected,
            reason=reason,
            reversible=reversible,
        )
        self.log_entries.append(entry)
        logger.info(
            "Cleaning [%s]: col=%s, rows %d->%d, affected=%d, reason='%s'",
            operation,
            target_column,
            rows_before,
            rows_after,
            values_affected,
            reason,
        )

    def standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardizes column names to lowercase and underscores if configured."""
        if not self.config.get("standardize_column_names", False):
            return df

        r_before = len(df)
        old_cols = list(df.columns)
        new_cols = [
            re.sub(r"[^\w\s]", "", c).strip().lower().replace(" ", "_").replace("-", "_")
            for c in old_cols
        ]
        df = df.copy()
        df.columns = new_cols
        changed_count = sum(1 for o, n in zip(old_cols, new_cols) if o != n)

        self._log(
            operation="standardize_column_names",
            target_column=None,
            rows_before=r_before,
            rows_after=r_before,
            values_affected=changed_count,
            reason="Standardized column headers to snake_case",
            reversible=True,
        )
        return df

    def handle_sentinel_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Replaces sentinel markers like '?' with np.nan."""
        sentinels = self.config.get("sentinel_values", ["?", "None", "NULL", "Unknown/Invalid"])
        r_before = len(df)
        df = df.copy()

        total_replaced = 0
        for col in df.columns:
            if df[col].dtype == object or isinstance(df[col].dtype, pd.StringDtype):
                str_series = df[col].astype(str).str.strip()
                mask = str_series.isin(sentinels)
                count = int(mask.sum())
                if count > 0:
                    df.loc[mask, col] = np.nan
                    total_replaced += count
                    self._log(
                        operation="replace_sentinels",
                        target_column=col,
                        rows_before=r_before,
                        rows_after=r_before,
                        values_affected=count,
                        reason=f"Replaced sentinel values {sentinels} with NaN",
                        reversible=False,
                    )
        return df

    def remove_exact_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Removes exact duplicate rows if enabled in configuration."""
        if not self.config.get("drop_exact_duplicates", True):
            return df

        r_before = len(df)
        dups_count = int(df.duplicated().sum())
        if dups_count > 0:
            df = df.drop_duplicates().copy()
            r_after = len(df)
            self._log(
                operation="remove_exact_duplicates",
                target_column=None,
                rows_before=r_before,
                rows_after=r_after,
                values_affected=dups_count,
                reason="Removed completely identical duplicate rows",
                reversible=False,
            )
        return df

    def handle_patient_encounters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handles repeated encounters for the same patient according to config."""
        strategy = self.config.get("patient_deduplication", "keep_all")
        patient_col = self.schema.get("patient_id", "patient_nbr")

        if strategy == "keep_first" and patient_col in df.columns:
            r_before = len(df)
            dups = int(df.duplicated(subset=[patient_col], keep="first").sum())
            if dups > 0:
                df = df.drop_duplicates(subset=[patient_col], keep="first").copy()
                r_after = len(df)
                self._log(
                    operation="deduplicate_patients_keep_first",
                    target_column=patient_col,
                    rows_before=r_before,
                    rows_after=r_after,
                    values_affected=dups,
                    reason="Retained only the initial hospital encounter per unique patient",
                    reversible=False,
                )
        return df

    def handle_sparse_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drops columns with extreme missingness specified in config (e.g. weight, payer_code)."""
        sparse_cols = self.config.get("columns_to_drop_if_sparse", ["weight", "payer_code"])
        r_before = len(df)
        df = df.copy()

        for col in sparse_cols:
            if col in df.columns:
                missing_pct = df[col].isna().sum() / len(df)
                # Drop only if missingness exceeds threshold (e.g. > 50%)
                threshold = self.config.get("high_missing_threshold", 0.50)
                if missing_pct >= threshold:
                    df = df.drop(columns=[col])
                    self._log(
                        operation="drop_sparse_column",
                        target_column=col,
                        rows_before=r_before,
                        rows_after=r_before,
                        values_affected=r_before,
                        reason=f"Dropped column '{col}' due to high missingness ({missing_pct:.1%})",
                        reversible=False,
                    )
        return df

    def map_id_descriptions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Maps numeric categorical IDs to readable clinical descriptions."""
        if not self.id_mappings:
            return df

        df = df.copy()
        r_len = len(df)

        for col, mapping in self.id_mappings.items():
            if col in df.columns and mapping:
                desc_col = f"{col}_desc"
                # Map using int conversion where possible
                numeric_series = pd.to_numeric(df[col], errors="coerce")
                mapped_series = numeric_series.map(mapping)
                # Fill unmapped with raw or unknown
                mapped_series = mapped_series.fillna("Unknown / Other")
                df[desc_col] = mapped_series
                self._log(
                    operation="map_id_descriptions",
                    target_column=desc_col,
                    rows_before=r_len,
                    rows_after=r_len,
                    values_affected=len(mapped_series),
                    reason=f"Created human-readable descriptor column '{desc_col}' from '{col}'",
                    reversible=True,
                )
        return df

    def group_icd9_diagnoses(self, df: pd.DataFrame) -> pd.DataFrame:
        """Groups ICD-9 primary diagnosis codes (diag_1) into standard clinical categories."""
        if not self.config.get("icd9_grouping_enabled", True) or "diag_1" not in df.columns:
            return df

        def categorize_icd9(val: Any) -> str:
            if pd.isna(val):
                return "Missing"
            val_str = str(val).strip()
            if not val_str or val_str in ("?", "None", "NULL"):
                return "Missing"

            # Check E and V codes (supplementary classifications)
            if val_str.startswith("E") or val_str.startswith("V"):
                return "Other / External"

            # Try parsing numeric prefix
            try:
                code_num = float(val_str)
            except ValueError:
                # In case of codes like '250.01' or non-standard characters
                match = re.match(r"^(\d+)", val_str)
                if match:
                    code_num = float(match.group(1))
                else:
                    return "Other"

            # ICD-9 Classification Ranges
            if (390 <= code_num <= 459) or code_num == 785:
                return "Circulatory"
            elif (460 <= code_num <= 519) or code_num == 786:
                return "Respiratory"
            elif (520 <= code_num <= 579) or code_num == 787:
                return "Digestive"
            elif 250 <= code_num < 251:
                return "Diabetes"
            elif 800 <= code_num <= 999:
                return "Injury / Poisoning"
            elif 710 <= code_num <= 739:
                return "Musculoskeletal"
            elif (580 <= code_num <= 629) or code_num == 788:
                return "Genitourinary"
            elif 140 <= code_num <= 239:
                return "Neoplasms"
            else:
                return "Other"

        r_len = len(df)
        df = df.copy()
        df["diag_1_group"] = df["diag_1"].apply(categorize_icd9)

        self._log(
            operation="icd9_grouping",
            target_column="diag_1_group",
            rows_before=r_len,
            rows_after=r_len,
            values_affected=r_len,
            reason="Mapped ICD-9 primary diagnosis (diag_1) into high-level clinical disease groups",
            reversible=True,
        )
        return df

    def enforce_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converts numerical and categorical columns to appropriate types."""
        df = df.copy()
        r_len = len(df)

        num_cols = self.schema.get("numerical_columns", [])
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        self._log(
            operation="enforce_data_types",
            target_column=None,
            rows_before=r_len,
            rows_after=r_len,
            values_affected=len(num_cols),
            reason="Coerced numerical columns to float/int representations",
            reversible=False,
        )
        return df

    def clean(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list[CleaningLogEntry]]:
        """Executes the complete cleaning pipeline on raw encounter data.

        Returns:
            Tuple of (cleaned_dataframe, list of CleaningLogEntry).
        """
        logger.info("Executing cleaning pipeline on %d rows...", len(df))
        self.log_entries.clear()

        df_cleaned = df.copy()
        df_cleaned = self.standardize_column_names(df_cleaned)
        df_cleaned = self.handle_sentinel_values(df_cleaned)
        df_cleaned = self.remove_exact_duplicates(df_cleaned)
        df_cleaned = self.handle_patient_encounters(df_cleaned)
        df_cleaned = self.handle_sparse_columns(df_cleaned)
        df_cleaned = self.map_id_descriptions(df_cleaned)
        df_cleaned = self.group_icd9_diagnoses(df_cleaned)
        df_cleaned = self.enforce_data_types(df_cleaned)

        logger.info(
            "Cleaning completed: input %d rows -> output %d rows. %d log entries recorded.",
            len(df),
            len(df_cleaned),
            len(self.log_entries),
        )

        return df_cleaned, list(self.log_entries)

    def get_log_dataframe(self) -> pd.DataFrame:
        """Returns the cleaning log as a pandas DataFrame."""
        if not self.log_entries:
            return pd.DataFrame(
                columns=[
                    "timestamp",
                    "operation",
                    "target_column",
                    "rows_before",
                    "rows_after",
                    "values_affected",
                    "reason",
                    "reversible",
                ]
            )
        return pd.DataFrame([e.to_dict() for e in self.log_entries])
