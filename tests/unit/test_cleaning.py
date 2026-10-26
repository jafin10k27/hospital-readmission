"""Unit tests for Data Cleaning Module (FR-3)."""

import pandas as pd

from hospital_readmission.cleaning import CleaningPipeline
from tests.fixtures.synthetic_encounters import create_synthetic_raw_dataframe


def test_sentinel_replacement_with_nan():
    """Verifies that '?' sentinel values are converted to np.nan and logged."""
    df = create_synthetic_raw_dataframe()
    cleaner = CleaningPipeline(config={"sentinel_values": ["?"]})

    cleaned_df = cleaner.handle_sentinel_values(df)

    # 'race' row 2 was '?'
    assert pd.isna(cleaned_df.loc[2, "race"])
    # Verify logging
    entries = cleaner.log_entries
    race_log = [e for e in entries if e.target_column == "race"]
    assert len(race_log) == 1
    assert race_log[0].values_affected == 1


def test_remove_exact_duplicates():
    """Verifies exact duplicate removal with row count logging."""
    df = create_synthetic_raw_dataframe()
    assert len(df) == 10

    cleaner = CleaningPipeline(config={"drop_exact_duplicates": True})
    cleaned_df = cleaner.remove_exact_duplicates(df)

    assert len(cleaned_df) == 9
    dup_logs = [e for e in cleaner.log_entries if e.operation == "remove_exact_duplicates"]
    assert len(dup_logs) == 1
    assert dup_logs[0].rows_before == 10
    assert dup_logs[0].rows_after == 9
    assert dup_logs[0].values_affected == 1


def test_drop_sparse_columns():
    """Verifies dropping of columns with missingness exceeding threshold."""
    df = create_synthetic_raw_dataframe()
    cleaner = CleaningPipeline(
        config={
            "sentinel_values": ["?"],
            "columns_to_drop_if_sparse": ["weight", "payer_code"],
            "high_missing_threshold": 0.50,
        }
    )
    # First replace sentinels to NaN
    df_na = cleaner.handle_sentinel_values(df)
    df_sparse = cleaner.handle_sparse_columns(df_na)

    assert "weight" not in df_sparse.columns
    assert "payer_code" not in df_sparse.columns
    assert "encounter_id" in df_sparse.columns


def test_icd9_clinical_grouping():
    """Verifies that ICD-9 primary diagnosis codes map to recognized clinical clusters."""
    df = pd.DataFrame({
        "diag_1": ["414", "428", "250.01", "486", "584", "820", "715", "174", "V58"]
    })
    cleaner = CleaningPipeline(config={"icd9_grouping_enabled": True})
    df_grouped = cleaner.group_icd9_diagnoses(df)

    assert df_grouped.loc[0, "diag_1_group"] == "Circulatory"   # 414
    assert df_grouped.loc[1, "diag_1_group"] == "Circulatory"   # 428
    assert df_grouped.loc[2, "diag_1_group"] == "Diabetes"      # 250
    assert df_grouped.loc[3, "diag_1_group"] == "Respiratory"   # 486
    assert df_grouped.loc[4, "diag_1_group"] == "Genitourinary" # 584
    assert df_grouped.loc[5, "diag_1_group"] == "Injury / Poisoning" # 820
    assert df_grouped.loc[6, "diag_1_group"] == "Musculoskeletal"    # 715
    assert df_grouped.loc[7, "diag_1_group"] == "Neoplasms"          # 174
    assert df_grouped.loc[8, "diag_1_group"] == "Other / External"   # V58


def test_patient_deduplication_strategy():
    """Verifies that 'keep_first' keeps only the first encounter per patient."""
    df = create_synthetic_raw_dataframe()
    cleaner = CleaningPipeline(
        config={"patient_deduplication": "keep_first"},
        schema={"patient_id": "patient_nbr"},
    )
    dedup_df = cleaner.handle_patient_encounters(df)

    # 7 unique patients in synthetic fixture
    assert dedup_df["patient_nbr"].nunique() == len(dedup_df)
    assert len(dedup_df) == 7
