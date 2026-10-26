"""Readmission Outcome Definition Module (FR-5).

Defines, validates, and binarizes the 30-day hospital readmission target variable
while preserving the original categorical outcome column and verifying integrity.
"""

from dataclasses import dataclass

import pandas as pd

from hospital_readmission.logging_config import setup_logger

logger = setup_logger(__name__)


class OutcomeDefinitionError(Exception):
    """Raised when the 30-day readmission outcome cannot be reliably determined."""
    pass


@dataclass
class OutcomeSummary:
    """Summary metrics of the readmission outcome."""

    total_encounters: int
    readmitted_30d_count: int
    readmission_rate_pct: float
    raw_distribution: dict[str, int]
    raw_percentages: dict[str, float]
    outcome_column: str
    target_column: str
    is_valid: bool
    notes: str


def define_readmission_outcome(
    df: pd.DataFrame,
    outcome_col: str = "readmitted",
    target_col: str = "readmitted_30d",
    positive_values: list[str] | None = None,
    negative_values: list[str] | None = None,
) -> tuple[pd.DataFrame, OutcomeSummary]:
    """Binarizes the 30-day readmission outcome according to clinical criteria.

    For UCI Diabetes 130-US Hospitals dataset:
        '<30' -> 1 (Readmitted within 30 days)
        '>30' -> 0 (Readmitted after 30 days, not a 30-day readmission)
        'NO'  -> 0 (No recorded readmission)

    Args:
        df: Input DataFrame containing the encounter records.
        outcome_col: Name of the existing outcome column.
        target_col: Name of the binary target column to create.
        positive_values: List of string labels indicating 30-day readmission (default: ['<30']).
        negative_values: List of string labels indicating negative outcome (default: ['>30', 'NO']).

    Returns:
        Tuple of (DataFrame with target_col added, OutcomeSummary).

    Raises:
        OutcomeDefinitionError: If the outcome column is missing or labels are unrecognizable.
    """
    if outcome_col not in df.columns:
        raise OutcomeDefinitionError(
            f"Required outcome column '{outcome_col}' is missing from the dataset. "
            "Cannot calculate 30-day readmission without a valid outcome label."
        )

    pos_vals = set(positive_values or ["<30"])
    neg_vals = set(negative_values or [">30", "NO"])

    df = df.copy()
    raw_series = df[outcome_col].astype(str).str.strip()

    # Verify that valid labels are present
    unique_labels = set(raw_series.unique())
    valid_labels = pos_vals | neg_vals

    unrecognized = unique_labels - valid_labels
    if unrecognized:
        logger.warning(
            "Found unrecognized outcome labels: %s. Expected only %s",
            unrecognized,
            valid_labels,
        )

    # Compute raw counts
    raw_counts = raw_series.value_counts().to_dict()
    total = len(df)
    raw_pcts = {k: round((v / total) * 100, 2) for k, v in raw_counts.items()}

    # Map to binary target
    def map_outcome(val: str) -> int:
        if val in pos_vals:
            return 1
        elif val in neg_vals:
            return 0
        else:
            return 0  # Treat unrecognized as negative or log warning

    df[target_col] = raw_series.apply(map_outcome).astype(int)

    pos_count = int((df[target_col] == 1).sum())
    pos_rate = round((pos_count / total) * 100, 2) if total > 0 else 0.0

    notes = (
        "30-day readmission defined strictly from encounter labels where '<30' = 1, "
        "and '>30' or 'NO' = 0. Notice: Absence of recorded readmission reflects "
        "dataset scope and does not prove absence of care transitions outside the participating health systems."
    )

    summary = OutcomeSummary(
        total_encounters=total,
        readmitted_30d_count=pos_count,
        readmission_rate_pct=pos_rate,
        raw_distribution=raw_counts,
        raw_percentages=raw_pcts,
        outcome_column=outcome_col,
        target_column=target_col,
        is_valid=True,
        notes=notes,
    )

    logger.info(
        "Readmission outcome configured: %d encounters, %d 30-day readmissions (%.2f%%)",
        total,
        pos_count,
        pos_rate,
    )

    return df, summary
