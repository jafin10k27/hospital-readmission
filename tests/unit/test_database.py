"""Unit tests for SQLite Database and SQL Analytics (FR-4)."""

from pathlib import Path

import pandas as pd
import pytest

from hospital_readmission.database import DatabaseManager
from hospital_readmission.outcomes import define_readmission_outcome
from hospital_readmission.sql_queries import SQLAnalyticsService
from tests.fixtures.synthetic_encounters import create_synthetic_raw_dataframe


@pytest.fixture
def test_db(tmp_path: Path) -> DatabaseManager:
    """Fixture providing an initialized SQLite test database."""
    db_path = tmp_path / "test_encounters.db"
    db = DatabaseManager(db_path)
    db.init_schema()

    raw_df = create_synthetic_raw_dataframe()
    df_out, _ = define_readmission_outcome(raw_df)
    db.store_encounters(df_out, table_name="encounters")
    return db


def test_overview_sql_metrics(test_db: DatabaseManager):
    """Verifies headline SQL metrics on synthetic fixture."""
    service = SQLAnalyticsService(test_db)
    metrics = service.get_overview_metrics()

    assert metrics["total_encounters"] == 10
    assert metrics["unique_patients"] == 7
    assert metrics["readmitted_30d_count"] == 3
    assert metrics["readmission_rate_pct"] == 30.0


def test_sql_rate_by_dimension(test_db: DatabaseManager):
    """Verifies parameterized aggregation query by age group."""
    service = SQLAnalyticsService(test_db)
    df_age = service.get_rate_by_dimension("age")

    assert not df_age.empty
    assert "age" in df_age.columns
    assert "readmission_rate_pct" in df_age.columns
    assert "total_encounters" in df_age.columns


def test_destructive_sql_prohibition(test_db: DatabaseManager):
    """Verifies that destructive SQL commands are blocked with PermissionError."""
    service = SQLAnalyticsService(test_db)

    with pytest.raises(PermissionError, match="Destructive operations"):
        service.run_custom_query("DROP TABLE encounters;")

    with pytest.raises(PermissionError, match="Destructive operations"):
        service.run_custom_query("DELETE FROM encounters WHERE encounter_id = 1;")

    with pytest.raises(PermissionError, match="Destructive operations"):
        service.run_custom_query("UPDATE encounters SET readmitted_30d = 0;")


def test_safe_custom_sql_execution(test_db: DatabaseManager):
    """Verifies successful execution of valid read-only SELECT statements."""
    service = SQLAnalyticsService(test_db)
    query = "SELECT age, COUNT(*) AS cnt FROM encounters GROUP BY age ORDER BY cnt DESC;"
    res = service.run_custom_query(query)

    assert isinstance(res, pd.DataFrame)
    assert len(res) > 0
    assert "cnt" in res.columns
