"""Unit tests for Data Ingestion Module (FR-1)."""

from pathlib import Path

import pandas as pd
import pytest

from hospital_readmission.ingestion import (
    DataIngestionError,
    DatasetLoader,
    load_id_mappings,
)
from tests.fixtures.synthetic_encounters import save_synthetic_csv


def test_successful_csv_ingestion(tmp_path: Path):
    """Verifies that a valid CSV is loaded with accurate row/col metadata."""
    csv_file = tmp_path / "valid_data.csv"
    save_synthetic_csv(csv_file)

    loader = DatasetLoader()
    df, meta = loader.load_csv(csv_file)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 10
    assert len(df.columns) == 50
    assert meta.row_count == 10
    assert meta.column_count == 50
    assert meta.encoding_used in ("utf-8", "latin-1")
    assert "encounter_id" in meta.columns


def test_missing_file_error(tmp_path: Path):
    """Verifies DataIngestionError when file does not exist."""
    non_existent = tmp_path / "does_not_exist.csv"
    loader = DatasetLoader()

    with pytest.raises(DataIngestionError, match="does not exist"):
        loader.load_csv(non_existent)


def test_empty_file_error(tmp_path: Path):
    """Verifies DataIngestionError when file is 0 bytes."""
    empty_file = tmp_path / "empty.csv"
    empty_file.touch()

    loader = DatasetLoader()
    with pytest.raises(DataIngestionError, match="empty"):
        loader.load_csv(empty_file)


def test_unsupported_extension_error(tmp_path: Path):
    """Verifies DataIngestionError when file format is not .csv or .txt."""
    bad_file = tmp_path / "data.xlsx"
    bad_file.write_text("dummy")

    loader = DatasetLoader()
    with pytest.raises(DataIngestionError, match="Unsupported file format"):
        loader.load_csv(bad_file)


def test_load_csv_with_nrows_limit(tmp_path: Path):
    """Verifies that nrows parameter restricts loaded rows correctly."""
    csv_file = tmp_path / "data_limit.csv"
    save_synthetic_csv(csv_file)

    loader = DatasetLoader()
    df, meta = loader.load_csv(csv_file, nrows=3)

    assert len(df) == 3
    assert meta.row_count == 3
    assert meta.extra_info.get("preview_only") is True


def test_load_id_mappings(tmp_path: Path):
    """Verifies parsing of multi-section IDS_mapping.csv."""
    map_file = tmp_path / "test_IDS_mapping.csv"
    content = """admission_type_id,description
1,Emergency
2,Urgent

discharge_disposition_id,description
1,Discharged to home
2,Transferred

admission_source_id,description
7,Emergency Room
"""
    map_file.write_text(content)

    mappings = load_id_mappings(map_file)
    assert 1 in mappings["admission_type_id"]
    assert mappings["admission_type_id"][1] == "Emergency"
    assert mappings["discharge_disposition_id"][2] == "Transferred"
    assert mappings["admission_source_id"][7] == "Emergency Room"
