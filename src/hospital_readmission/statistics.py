"""Statistical Inference and Hypothesis Testing Module (FR-7).

Implements rigorous hypothesis testing, confidence intervals (Wilson score),
effect sizes (Cramer's V, Rank-Biserial correlation), and multiple-testing corrections
(Benjamini-Hochberg FDR, Bonferroni).
"""

import math
from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd
from scipy import stats

from hospital_readmission.logging_config import setup_logger

logger = setup_logger(__name__)


@dataclass
class ProportionCI:
    """Wilson Score confidence interval for a proportion."""

    rate: float
    ci_lower: float
    ci_upper: float
    numerator: int
    denominator: int


def calculate_wilson_ci(
    k: int,
    n: int,
    confidence: float = 0.95,
) -> ProportionCI:
    """Calculates Wilson score interval for binomial proportion with continuity correction.

    Wilson score interval has superior coverage properties for low/high base rates
    compared to normal approximation (Wald interval).
    """
    if n <= 0:
        return ProportionCI(rate=0.0, ci_lower=0.0, ci_upper=0.0, numerator=0, denominator=0)

    p = k / n
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    z2 = z * z

    denominator = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denominator
    half_width = (z / denominator) * math.sqrt((p * (1 - p) / n) + (z2 / (4 * n * n)))

    lower = max(0.0, center - half_width)
    upper = min(1.0, center + half_width)

    return ProportionCI(
        rate=round(p * 100, 2),
        ci_lower=round(lower * 100, 2),
        ci_upper=round(upper * 100, 2),
        numerator=k,
        denominator=n,
    )


@dataclass
class CategoricalTestResult:
    """Result of Chi-Square test of independence."""

    variable: str
    test_name: str
    chi2_stat: float
    p_value: float
    degrees_of_freedom: int
    cramers_v: float
    effect_size_label: str
    min_expected_count: float
    is_valid_chi2: bool
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NumericalTestResult:
    """Result of two-sample comparison (Mann-Whitney U and Welch t-test)."""

    variable: str
    test_name: str
    statistic: float
    p_value: float
    readmitted_mean: float
    readmitted_median: float
    non_readmitted_mean: float
    non_readmitted_median: float
    effect_size: float
    effect_size_metric: str
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def perform_categorical_test(
    df: pd.DataFrame,
    var_col: str,
    outcome_col: str = "readmitted_30d",
) -> CategoricalTestResult:
    """Performs Chi-Square test of independence and calculates Cramer's V effect size."""
    clean_df = df[[var_col, outcome_col]].dropna()
    crosstab = pd.crosstab(clean_df[var_col], clean_df[outcome_col])

    if crosstab.shape[0] < 2 or crosstab.shape[1] < 2:
        return CategoricalTestResult(
            variable=var_col,
            test_name="Chi-Square Test",
            chi2_stat=0.0,
            p_value=1.0,
            degrees_of_freedom=0,
            cramers_v=0.0,
            effect_size_label="None / Degenerate",
            min_expected_count=0.0,
            is_valid_chi2=False,
            interpretation="Insufficient categories for Chi-Square test.",
        )

    chi2, p, dof, expected = stats.chi2_contingency(crosstab)
    n = clean_df.shape[0]
    min_exp = float(expected.min())
    is_valid = min_exp >= 5.0

    # Cramer's V calculation: sqrt(chi2 / (n * min(r-1, k-1)))
    r, k = crosstab.shape
    min_dim = min(r - 1, k - 1)
    cramers_v = math.sqrt(chi2 / (n * min_dim)) if n > 0 and min_dim > 0 else 0.0

    # Qualitative effect size label
    if cramers_v < 0.10:
        eff_label = "Negligible"
    elif cramers_v < 0.30:
        eff_label = "Small"
    elif cramers_v < 0.50:
        eff_label = "Medium"
    else:
        eff_label = "Large"

    interp = (
        f"Chi-square test {'is statistically significant' if p < 0.05 else 'is not statistically significant'} "
        f"(p={p:.2e}, Cramer's V={cramers_v:.3f} [{eff_label}]). "
        f"{'Assumptions met (min expected cell >= 5).' if is_valid else 'Caution: low expected cell counts.'}"
    )

    return CategoricalTestResult(
        variable=var_col,
        test_name="Chi-Square Test",
        chi2_stat=round(float(chi2), 3),
        p_value=float(p),
        degrees_of_freedom=int(dof),
        cramers_v=round(float(cramers_v), 3),
        effect_size_label=eff_label,
        min_expected_count=round(min_exp, 2),
        is_valid_chi2=is_valid,
        interpretation=interp,
    )


def perform_numerical_test(
    df: pd.DataFrame,
    num_col: str,
    outcome_col: str = "readmitted_30d",
) -> NumericalTestResult:
    """Performs Mann-Whitney U test (non-parametric) comparing readmitted vs. non-readmitted encounters."""
    sub = df[[num_col, outcome_col]].dropna()
    series_num = pd.to_numeric(sub[num_col], errors="coerce")
    sub = sub.loc[series_num.notna()].copy()
    sub[num_col] = series_num

    group_readmitted = sub[sub[outcome_col] == 1][num_col]
    group_non_readmitted = sub[sub[outcome_col] == 0][num_col]

    n1 = len(group_readmitted)
    n2 = len(group_non_readmitted)

    if n1 == 0 or n2 == 0:
        return NumericalTestResult(
            variable=num_col,
            test_name="Mann-Whitney U",
            statistic=0.0,
            p_value=1.0,
            readmitted_mean=0.0,
            readmitted_median=0.0,
            non_readmitted_mean=0.0,
            non_readmitted_median=0.0,
            effect_size=0.0,
            effect_size_metric="Rank-Biserial",
            interpretation="Insufficient data in one or both outcome groups.",
        )

    res = stats.mannwhitneyu(group_readmitted, group_non_readmitted, alternative="two-sided")
    # Rank biserial correlation = 1 - (2*U) / (n1 * n2)
    u_stat = float(res.statistic)
    rank_biserial = 1.0 - (2.0 * u_stat) / (n1 * n2)

    interp = (
        f"Non-parametric Mann-Whitney U test {'indicates a significant rank difference' if res.pvalue < 0.05 else 'shows no significant rank difference'} "
        f"(U={u_stat:,.0f}, p={res.pvalue:.2e}, rank-biserial r={rank_biserial:.3f})."
    )

    return NumericalTestResult(
        variable=num_col,
        test_name="Mann-Whitney U Test",
        statistic=round(u_stat, 1),
        p_value=float(res.pvalue),
        readmitted_mean=round(float(group_readmitted.mean()), 2),
        readmitted_median=round(float(group_readmitted.median()), 2),
        non_readmitted_mean=round(float(group_non_readmitted.mean()), 2),
        non_readmitted_median=round(float(group_non_readmitted.median()), 2),
        effect_size=round(float(rank_biserial), 3),
        effect_size_metric="Rank-Biserial Correlation",
        interpretation=interp,
    )


def adjust_p_values(
    p_values: list[float],
    method: str = "fdr_bh",
) -> list[float]:
    """Applies multiple testing correction (Benjamini-Hochberg FDR or Bonferroni)."""
    m = len(p_values)
    if m <= 1:
        return p_values

    if method == "bonferroni":
        return [min(1.0, p * m) for p in p_values]

    # Benjamini-Hochberg False Discovery Rate (FDR)
    indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * m
    cum_min = 1.0

    for rank, (original_idx, p_val) in reversed(list(enumerate(indexed_p, start=1))):
        val = min(1.0, (p_val * m) / rank)
        cum_min = min(cum_min, val)
        adjusted[original_idx] = cum_min

    return adjusted
