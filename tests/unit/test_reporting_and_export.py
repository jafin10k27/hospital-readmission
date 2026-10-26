"""Unit tests for Reporting and Export Modules (FR-10, FR-11)."""

import json
from pathlib import Path

import pandas as pd

from hospital_readmission.export import export_dataframe_csv, export_metadata_json
from hospital_readmission.reporting import ReportGenerator


def test_html_report_generation(tmp_path: Path):
    """Verifies that Jinja2 HTML report renders with accurate dynamic data."""
    reporter = ReportGenerator(tmp_path)
    data = {
        "dataset_name": "Synthetic Encounter Fixture",
        "total_encounters": 100,
        "unique_patients": 80,
        "readmission_rate": 15.5,
        "readmitted_count": 15,
        "exact_duplicates": 2,
        "columns_with_missing": 3,
        "cleaning_ops_count": 5,
        "associations_table": [
            {
                "category": "[70-80)",
                "total_encounters": 40,
                "readmission_rate_pct": 20.0,
                "ci_lower_pct": 10.5,
                "ci_upper_pct": 34.0,
            }
        ],
    }

    out_file = reporter.generate_html_report(data, filename="test_report.html")
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "Synthetic Encounter Fixture" in content
    assert "15.50%" in content
    assert "Exploratory Clinical Disclaimer" in content


def test_pdf_report_generation(tmp_path: Path):
    """Verifies ReportLab PDF report generation."""
    reporter = ReportGenerator(tmp_path)
    data = {
        "total_encounters": 50,
        "unique_patients": 45,
        "readmitted_count": 5,
        "readmission_rate": 10.0,
        "associations_table": [
            {
                "category": "Emergency",
                "total_encounters": 30,
                "readmission_rate_pct": 12.0,
                "ci_lower_pct": 5.0,
                "ci_upper_pct": 25.0,
            }
        ],
    }

    pdf_file = reporter.generate_pdf_report(data, filename="test_report.pdf")
    assert pdf_file.exists()
    assert pdf_file.stat().st_size > 500


def test_export_utilities(tmp_path: Path):
    """Verifies CSV and JSON export functions."""
    df = pd.DataFrame({"colA": [1, 2], "colB": ["x", "y"]})
    csv_path = tmp_path / "export" / "data.csv"
    res_csv = export_dataframe_csv(df, csv_path)
    assert res_csv.exists()
    assert len(pd.read_csv(res_csv)) == 2

    meta = {"key": "value", "count": 42}
    json_path = tmp_path / "export" / "meta.json"
    res_json = export_metadata_json(meta, json_path)
    assert res_json.exists()
    with open(res_json) as f:
        loaded = json.load(f)
    assert loaded["count"] == 42
