"""Unit tests for Readmission Outcome Module (FR-5)."""

import pandas as pd
import pytest

from hospital_readmission.outcomes import (
    OutcomeDefinitionError,
    define_readmission_outcome,
)
from tests.fixtures.synthetic_encounters import create_synthetic_raw_dataframe


def test_correct_30d_outcome_mapping():
    """Verifies that '<30' maps to 1, and '>30' or 'NO' map to 0."""
    df = create_synthetic_raw_dataframe()
    df_out, summary = define_readmission_outcome(df)

    assert "readmitted_30d" in df_out.columns
    # Rows 0, 1, 4 have '<30'
    assert df_out.loc[0, "readmitted_30d"] == 1
    assert df_out.loc[1, "readmitted_30d"] == 1
    assert df_out.loc[4, "readmitted_30d"] == 1
    # Rows 2, 5, 7, 9 have '>30' -> 0
    assert df_out.loc[2, "readmitted_30d"] == 0
    assert df_out.loc[5, "readmitted_30d"] == 0
    # Rows 3, 6, 8 have 'NO' -> 0
    assert df_out.loc[3, "readmitted_30d"] == 0
    assert df_out.loc[6, "readmitted_30d"] == 0

    assert summary.readmitted_30d_count == 3
    assert summary.total_encounters == 10
    assert summary.readmission_rate_pct == 30.0


def test_missing_outcome_column_error():
    """Verifies OutcomeDefinitionError when outcome column is absent."""
    df = pd.DataFrame({"encounter_id": [1, 2], "age": ["[50-60)", "[60-70)"]})

    with pytest.raises(OutcomeDefinitionError, match="Required outcome column 'readmitted' is missing"):
        define_readmission_outcome(df, outcome_col="readmitted")


def test_preserves_original_outcome_column():
    """Verifies that original raw outcome column is retained unmodified."""
    df = create_synthetic_raw_dataframe()
    df_out, _ = define_readmission_outcome(df)

    assert "readmitted" in df_out.columns
    assert set(df_out["readmitted"].unique()) == {"<30", ">30", "NO"}
