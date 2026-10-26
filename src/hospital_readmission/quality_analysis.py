"""Data Quality Analysis Module (FR-2, FR-6).

Computes comprehensive missingness profiles, cardinality metrics,
and duplicate encounter distributions.
"""

from dataclasses import dataclass

import pandas as pd

from hospital_readmission.logging_config import setup_logger

logger = setup_logger(__name__)


@dataclass
class QualitySummary:
    """High-level summary of dataset quality."""

    total_rows: int
    total_columns: int
    total_cells: int
    total_missing_cells: int
    overall_missing_pct: float
    columns_with_missing: int
    exact_duplicate_rows: int
    unique_patients: int | None
    encounters_per_patient_avg: float | None


class QualityAnalyzer:
    """Calculates missingness tables, duplicate rates, and data health metrics."""

    def __init__(self, sentinel_values: list[str] | None = None):
        self.sentinel_values = sentinel_values or ["?", "None", "NULL", "Unknown/Invalid"]

    def compute_missingness_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Computes missing value count and percentage for every column."""
        total_rows = len(df)
        records = []

        for col in df.columns:
            series = df[col]
            standard_na = int(series.isna().sum())

            # Sentinel checks for text columns
            sentinel_count = 0
            if series.dtype == object or isinstance(series.dtype, pd.StringDtype):
                str_vals = series.astype(str).str.strip()
                sentinel_count = int(str_vals.isin(self.sentinel_values).sum())

            total_missing = standard_na + sentinel_count
            pct = round((total_missing / total_rows) * 100, 2) if total_rows > 0 else 0.0

            records.append(
                {
                    "column": col,
                    "dtype": str(series.dtype),
                    "standard_na": standard_na,
                    "sentinel_count": sentinel_count,
                    "total_missing": total_missing,
                    "missing_percentage": pct,
                    "completeness_percentage": round(100.0 - pct, 2),
                }
            )

        df_res = pd.DataFrame(records)
        return df_res.sort_values(by="missing_percentage", ascending=False).reset_index(drop=True)

    def compute_cardinality_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Computes unique value counts and flags constant or ultra-high cardinality columns."""
        total_rows = len(df)
        records = []

        for col in df.columns:
            series = df[col]
            n_unique = int(series.nunique(dropna=True))
            pct_unique = round((n_unique / total_rows) * 100, 2) if total_rows > 0 else 0.0

            status = "Normal"
            if n_unique <= 1:
                status = "Constant"
            elif pct_unique > 90 and total_rows > 100:
                status = "Identifier / High Cardinality"

            records.append(
                {
                    "column": col,
                    "dtype": str(series.dtype),
                    "unique_values": n_unique,
                    "unique_percentage": pct_unique,
                    "sample_values": ", ".join(map(str, series.dropna().unique()[:4])),
                    "status": status,
                }
            )

        return pd.DataFrame(records).sort_values(by="unique_values", ascending=False).reset_index(drop=True)

    def get_summary(
        self,
        df: pd.DataFrame,
        patient_col: str = "patient_nbr",
    ) -> QualitySummary:
        """Returns headline dataset quality metrics."""
        total_rows = len(df)
        total_cols = len(df.columns)
        total_cells = total_rows * total_cols

        miss_df = self.compute_missingness_table(df)
        total_missing = int(miss_df["total_missing"].sum())
        overall_miss_pct = round((total_missing / total_cells) * 100, 2) if total_cells > 0 else 0.0
        cols_with_miss = int((miss_df["total_missing"] > 0).sum())

        exact_dups = int(df.duplicated().sum())

        unique_p = None
        enc_per_p = None
        if patient_col in df.columns:
            unique_p = int(df[patient_col].nunique())
            enc_per_p = round(total_rows / unique_p, 2) if unique_p > 0 else None

        return QualitySummary(
            total_rows=total_rows,
            total_columns=total_cols,
            total_cells=total_cells,
            total_missing_cells=total_missing,
            overall_missing_pct=overall_miss_pct,
            columns_with_missing=cols_with_miss,
            exact_duplicate_rows=exact_dups,
            unique_patients=unique_p,
            encounters_per_patient_avg=enc_per_p,
        )
