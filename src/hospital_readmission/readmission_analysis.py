"""Readmission Association Analysis Module (FR-7).

Analyzes clinical, demographic, utilization, and medication variables
in association with 30-day hospital readmissions with confidence intervals,
effect sizes, and multiple-comparison adjustments.
"""

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from hospital_readmission.logging_config import setup_logger
from hospital_readmission.statistics import (
    adjust_p_values,
    calculate_wilson_ci,
    perform_categorical_test,
    perform_numerical_test,
)

logger = setup_logger(__name__)


@dataclass
class GroupRateRecord:
    """Readmission metrics for a discrete group or category."""

    category: str
    total_encounters: int
    readmitted_count: int
    readmission_rate_pct: float
    ci_lower_pct: float
    ci_upper_pct: float
    percentage_of_cohort: float
    odds_ratio_vs_ref: float | None = None


class ReadmissionAnalyzer:
    """Orchestrates comprehensive 30-day readmission association analysis."""

    def __init__(self, target_col: str = "readmitted_30d"):
        self.target_col = target_col

    def calculate_group_rates(
        self,
        df: pd.DataFrame,
        group_col: str,
        reference_category: str | None = None,
        min_sample_size: int = 5,
    ) -> pd.DataFrame:
        """Calculates encounter counts, readmission rates, and 95% Wilson CIs for a column.

        Args:
            df: Cleaned encounter DataFrame.
            group_col: Categorical column to segment by.
            reference_category: Optional reference category for Odds Ratio calculation.
            min_sample_size: Minimum encounters for inclusion.

        Returns:
            DataFrame of group-level readmission metrics.
        """
        if group_col not in df.columns or self.target_col not in df.columns:
            return pd.DataFrame()

        clean = df[[group_col, self.target_col]].dropna().copy()
        clean[group_col] = clean[group_col].astype(str)
        total_cohort = len(clean)

        grouped = (
            clean.groupby(group_col)[self.target_col]
            .agg(
                total_encounters="count",
                readmitted_count="sum",
            )
            .reset_index()
        )

        # Filter small groups
        grouped = grouped[grouped["total_encounters"] >= min_sample_size].copy()
        if grouped.empty:
            return pd.DataFrame()

        # Compute Wilson Confidence Intervals
        records: list[GroupRateRecord] = []
        ref_odds = None

        if reference_category and reference_category in grouped[group_col].values:
            ref_row = grouped[grouped[group_col] == reference_category].iloc[0]
            r_k = int(ref_row["readmitted_count"])
            r_n = int(ref_row["total_encounters"])
            if (r_n - r_k) > 0 and r_k > 0:
                ref_odds = r_k / (r_n - r_k)

        for _, row in grouped.iterrows():
            cat = str(row[group_col])
            n = int(row["total_encounters"])
            k = int(row["readmitted_count"])
            ci = calculate_wilson_ci(k, n, confidence=0.95)
            cohort_pct = round((n / total_cohort) * 100, 2)

            or_val = None
            if ref_odds is not None and (n - k) > 0:
                cat_odds = k / (n - k)
                or_val = round(cat_odds / ref_odds, 2)

            records.append(
                GroupRateRecord(
                    category=cat,
                    total_encounters=n,
                    readmitted_count=k,
                    readmission_rate_pct=ci.rate,
                    ci_lower_pct=ci.ci_lower,
                    ci_upper_pct=ci.ci_upper,
                    percentage_of_cohort=cohort_pct,
                    odds_ratio_vs_ref=or_val,
                )
            )

        res_df = pd.DataFrame([asdict(r) for r in records])
        return res_df.sort_values(by="total_encounters", ascending=False).reset_index(drop=True)

    def run_all_categorical_tests(
        self,
        df: pd.DataFrame,
        categorical_columns: list[str],
    ) -> pd.DataFrame:
        """Executes Chi-Square tests across multiple candidate categorical predictors."""
        results: list[dict[str, Any]] = []

        valid_cols = [c for c in categorical_columns if c in df.columns]
        for col in valid_cols:
            res = perform_categorical_test(df, col, self.target_col)
            results.append(res.to_dict())

        if not results:
            return pd.DataFrame()

        res_df = pd.DataFrame(results)
        # Apply Benjamini-Hochberg FDR correction
        raw_p = res_df["p_value"].tolist()
        res_df["fdr_adjusted_p"] = adjust_p_values(raw_p, method="fdr_bh")
        res_df["bonferroni_p"] = adjust_p_values(raw_p, method="bonferroni")

        return res_df.sort_values(by="fdr_adjusted_p").reset_index(drop=True)

    def run_all_numerical_tests(
        self,
        df: pd.DataFrame,
        numerical_columns: list[str],
    ) -> pd.DataFrame:
        """Executes Mann-Whitney U rank tests across candidate numerical variables."""
        results: list[dict[str, Any]] = []

        valid_cols = [c for c in numerical_columns if c in df.columns]
        for col in valid_cols:
            res = perform_numerical_test(df, col, self.target_col)
            results.append(res.to_dict())

        if not results:
            return pd.DataFrame()

        res_df = pd.DataFrame(results)
        raw_p = res_df["p_value"].tolist()
        res_df["fdr_adjusted_p"] = adjust_p_values(raw_p, method="fdr_bh")
        res_df["bonferroni_p"] = adjust_p_values(raw_p, method="bonferroni")

        return res_df.sort_values(by="fdr_adjusted_p").reset_index(drop=True)
