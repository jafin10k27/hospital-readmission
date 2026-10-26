"""Unit tests for Schema and Data Validation Module (FR-2)."""

import pandas as pd

from hospital_readmission.schema_validation import DataValidator, Severity
from tests.fixtures.synthetic_encounters import create_synthetic_raw_dataframe


def test_validation_detects_exact_duplicates():
    """Verifies detection of exact duplicate rows."""
    df = create_synthetic_raw_dataframe()
    # Row 0 and Row 1 are identical in synthetic fixture
    validator = DataValidator()
    report = validator.validate(df)

    assert report.exact_duplicates == 1
    dup_issues = [i for i in report.issues if i.issue_type == "exact_duplicate_rows"]
    assert len(dup_issues) == 1
    assert dup_issues[0].severity == Severity.WARNING
    assert dup_issues[0].affected_rows == 1


def test_validation_detects_repeated_patients():
    """Verifies that patient visits are distinguished from exact row duplicates."""
    df = create_synthetic_raw_dataframe()
    validator = DataValidator()
    report = validator.validate(df)

    assert report.unique_patients == 7
    patient_issues = [i for i in report.issues if i.issue_type == "multiple_patient_encounters"]
    assert len(patient_issues) == 1
    assert patient_issues[0].severity == Severity.INFO
    assert "Distinguish exact duplicate rows" in patient_issues[0].recommended_action


def test_validation_detects_high_missingness():
    """Verifies detection of sentinel-based high missingness (e.g. weight, payer_code)."""
    df = create_synthetic_raw_dataframe()
    validator = DataValidator(sentinel_values=["?"])
    report = validator.validate(df)

    miss_issues = [i for i in report.issues if i.issue_type == "high_missingness"]
    miss_cols = {i.column for i in miss_issues}
    assert "weight" in miss_cols
    assert "payer_code" in miss_cols


def test_validation_detects_invalid_outcome_labels():
    """Verifies error severity if outcome column contains unrecognized labels."""
    df = create_synthetic_raw_dataframe()
    df.loc[0, "readmitted"] = "INVALID_CODE"

    validator = DataValidator()
    report = validator.validate(df)

    invalid_outcome_issues = [i for i in report.issues if i.issue_type == "invalid_outcome_labels"]
    assert len(invalid_outcome_issues) == 1
    assert invalid_outcome_issues[0].severity == Severity.ERROR


def test_validation_empty_dataframe():
    """Verifies behavior when dataset contains zero records."""
    empty_df = pd.DataFrame(columns=["encounter_id", "patient_nbr", "readmitted"])
    validator = DataValidator()
    report = validator.validate(empty_df)

    assert report.total_rows == 0
    assert report.error_count >= 1
    assert report.issues[0].issue_type == "empty_dataset"
