"""Unit tests for Statistical Inference and Hypothesis Testing (FR-7)."""

import pandas as pd
import pytest

from hospital_readmission.statistics import (
    adjust_p_values,
    calculate_wilson_ci,
    perform_categorical_test,
    perform_numerical_test,
)


def test_wilson_ci_accuracy_and_bounds():
    """Verifies Wilson score confidence interval calculation and boundary checks."""
    # Test standard case: 30 successes out of 100
    ci = calculate_wilson_ci(k=30, n=100, confidence=0.95)
    assert ci.rate == 30.0
    assert 21.0 <= ci.ci_lower <= 23.0
    assert 38.0 <= ci.ci_upper <= 41.0
    assert ci.ci_lower < ci.rate < ci.ci_upper

    # Boundary case: zero successes
    ci_zero = calculate_wilson_ci(k=0, n=50, confidence=0.95)
    assert ci_zero.rate == 0.0
    assert ci_zero.ci_lower == 0.0
    assert ci_zero.ci_upper > 0.0

    # Boundary case: zero denominator
    ci_empty = calculate_wilson_ci(k=0, n=0)
    assert ci_empty.rate == 0.0
    assert ci_empty.ci_lower == 0.0
    assert ci_empty.ci_upper == 0.0


def test_chi_square_independence_test():
    """Verifies Chi-Square test calculation and Cramer's V effect size."""
    # Construct synthetic 2x2 contingency table
    # Group A: 50 readmitted, 50 not (50%)
    # Group B: 10 readmitted, 90 not (10%)
    df = pd.DataFrame({
        "group": ["A"] * 100 + ["B"] * 100,
        "readmitted_30d": [1] * 50 + [0] * 50 + [1] * 10 + [0] * 90,
    })

    res = perform_categorical_test(df, "group", "readmitted_30d")

    assert res.p_value < 0.001
    assert res.chi2_stat > 30.0
    assert res.cramers_v > 0.30
    assert res.is_valid_chi2 is True


def test_mann_whitney_rank_sum_test():
    """Verifies non-parametric Mann-Whitney U test and rank-biserial correlation."""
    # Readmitted patients have higher prior utilization
    df = pd.DataFrame({
        "number_inpatient": [4, 5, 6, 3, 5, 4, 6] + [0, 1, 0, 0, 1, 0, 2],
        "readmitted_30d": [1] * 7 + [0] * 7,
    })

    res = perform_numerical_test(df, "number_inpatient", "readmitted_30d")

    assert res.p_value < 0.01
    assert res.readmitted_median > res.non_readmitted_median
    assert res.effect_size != 0.0


def test_fdr_and_bonferroni_adjustments():
    """Verifies multiple testing corrections."""
    raw_p = [0.001, 0.01, 0.03, 0.05, 0.20]

    # Bonferroni: multiply by m=5
    bonf = adjust_p_values(raw_p, method="bonferroni")
    assert bonf[0] == pytest.approx(0.005)
    assert bonf[1] == pytest.approx(0.05)
    assert bonf[4] == pytest.approx(1.0)

    # Benjamini-Hochberg FDR: monotonic non-decreasing
    fdr = adjust_p_values(raw_p, method="fdr_bh")
    assert fdr[0] < fdr[1] <= fdr[2] <= fdr[3] <= fdr[4]
    for orig, adj in zip(raw_p, fdr):
        assert adj >= orig
