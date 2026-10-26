"""Exploratory Data Analysis Module (FR-6).

Calculates parametric and non-parametric summary statistics, categorical frequencies,
correlation matrices, and cross-tabulations for clinical encounter attributes.
"""


import pandas as pd
from scipy import stats

from hospital_readmission.logging_config import setup_logger

logger = setup_logger(__name__)


class ExploratoryDataAnalyzer:
    """Computes descriptive and exploratory statistics from encounter records."""

    def __init__(self, numerical_cols: list[str] | None = None, categorical_cols: list[str] | None = None):
        self.numerical_cols = numerical_cols or []
        self.categorical_cols = categorical_cols or []

    def compute_numerical_summaries(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates robust descriptive statistics for numerical clinical variables."""
        # Find numeric columns available in df
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        # Filter out primary ID columns
        excluded_ids = {"encounter_id", "patient_nbr", "readmitted_30d"}
        target_cols = [c for c in num_cols if c not in excluded_ids]

        if not target_cols:
            return pd.DataFrame()

        records = []
        for col in target_cols:
            clean_series = pd.to_numeric(df[col], errors="coerce").dropna()
            if clean_series.empty:
                continue

            q25 = float(clean_series.quantile(0.25))
            q75 = float(clean_series.quantile(0.75))
            iqr = q75 - q25
            skewness = float(stats.skew(clean_series, nan_policy="omit"))

            records.append(
                {
                    "variable": col,
                    "count": int(len(clean_series)),
                    "mean": round(float(clean_series.mean()), 2),
                    "std": round(float(clean_series.std()), 2),
                    "median": round(float(clean_series.median()), 2),
                    "iqr": round(iqr, 2),
                    "q25": round(q25, 2),
                    "q75": round(q75, 2),
                    "min": round(float(clean_series.min()), 2),
                    "max": round(float(clean_series.max()), 2),
                    "skewness": round(skewness, 2),
                }
            )

        return pd.DataFrame(records).sort_values(by="variable").reset_index(drop=True)

    def compute_categorical_distribution(
        self,
        df: pd.DataFrame,
        column: str,
        top_n: int = 15,
    ) -> pd.DataFrame:
        """Returns frequency and proportion table for a categorical variable."""
        if column not in df.columns:
            return pd.DataFrame()

        series = df[column].fillna("Missing").astype(str)
        counts = series.value_counts(dropna=False).head(top_n)
        total = len(df)

        df_dist = pd.DataFrame(
            {
                "category": counts.index,
                "encounter_count": counts.values,
                "percentage": [round((c / total) * 100, 2) for c in counts.values],
            }
        )
        return df_dist

    def compute_correlation_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Computes Pearson and Spearman correlation matrix across numerical variables."""
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        excluded_ids = {"encounter_id", "patient_nbr"}
        target_cols = [c for c in num_cols if c not in excluded_ids]

        if len(target_cols) < 2:
            return pd.DataFrame()

        numeric_df = df[target_cols].apply(pd.to_numeric, errors="coerce")
        corr = numeric_df.corr(method="spearman").round(3)
        return corr
