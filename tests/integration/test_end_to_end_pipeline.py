"""Integration test for complete end-to-end pipeline execution."""

from pathlib import Path

import pytest

from hospital_readmission.config import AppConfig
from hospital_readmission.pipeline import HealthcarePipeline
from tests.fixtures.synthetic_encounters import save_synthetic_csv


def test_end_to_end_healthcare_pipeline(tmp_path: Path):
    """Executes the full pipeline on a synthetic benchmark fixture with known ground truth."""
    # 1. Setup paths
    raw_csv = tmp_path / "synthetic_diabetic_data.csv"
    save_synthetic_csv(raw_csv)

    db_path = tmp_path / "integration_test.db"
    reports_dir = tmp_path / "reports"

    config = AppConfig(
        raw_data_path=raw_csv,
        ids_mapping_path=tmp_path / "non_existent_ids.csv",
        processed_data_path=tmp_path / "cleaned.csv",
        database_path=db_path,
        reports_dir=reports_dir,
        logs_dir=tmp_path / "logs",
        settings={
            "cleaning": {
                "sentinel_values": ["?"],
                "columns_to_drop_if_sparse": ["weight", "payer_code"],
                "drop_exact_duplicates": True,
                "patient_deduplication": "keep_all",
            },
            "outcome": {
                "raw_column": "readmitted",
                "target_column": "readmitted_30d",
                "positive_values": ["<30"],
                "negative_values": [">30", "NO"],
            },
        },
        schema={"encounter_id": "encounter_id", "patient_id": "patient_nbr"},
    )

    pipeline = HealthcarePipeline(config=config)
    state = pipeline.run(file_path=raw_csv)

    # 2. Verify Ingestion & Validation
    assert state.ingestion_metadata.row_count == 10
    assert state.validation_report.exact_duplicates == 1

    # 3. Verify Cleaning
    # 1 exact duplicate removed -> 9 rows remain
    assert len(state.cleaned_df) == 9
    assert "weight" not in state.cleaned_df.columns
    assert "payer_code" not in state.cleaned_df.columns
    assert not state.cleaning_log_df.empty

    # 4. Verify Readmission Outcome
    # Out of 9 remaining rows, 2 were '<30' (row 0 kept, row 1 duplicate dropped, row 4 kept)
    assert state.outcome_summary.readmitted_30d_count == 2
    assert state.outcome_summary.readmission_rate_pct == pytest.approx(22.22, abs=0.1)

    # 5. Verify SQLite Persistence
    assert db_path.exists()
    df_sql = state.database_manager.execute_query("SELECT COUNT(*) AS total FROM encounters;")
    assert df_sql.iloc[0]["total"] == 9
