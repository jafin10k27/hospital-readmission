"""SQL Analytical Queries Module (FR-4).

Contains safe, parameterized SQL analytical queries for encounter metrics,
group aggregations, and readmission rate calculations.
"""

import re
from typing import Any

import pandas as pd

from hospital_readmission.database import DatabaseManager
from hospital_readmission.logging_config import setup_logger

logger = setup_logger(__name__)

# Predefined analytical queries
PREDEFINED_QUERIES = {
    "Overview Summary": """
        SELECT
            COUNT(*) AS total_encounters,
            COUNT(DISTINCT patient_nbr) AS unique_patients,
            ROUND(CAST(COUNT(*) AS REAL) / NULLIF(COUNT(DISTINCT patient_nbr), 0), 2) AS encounters_per_patient,
            SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_30d_count,
            ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
        FROM encounters;
    """,
    "Readmission by Age Group": """
        SELECT
            COALESCE(age, 'Unknown') AS age_group,
            COUNT(*) AS total_encounters,
            SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_count,
            ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
        FROM encounters
        GROUP BY age
        ORDER BY age;
    """,
    "Readmission by Admission Type": """
        SELECT
            COALESCE(admission_type_id_desc, 'Type ' || CAST(admission_type_id AS TEXT)) AS admission_type,
            COUNT(*) AS total_encounters,
            SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_count,
            ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
        FROM encounters
        GROUP BY admission_type
        ORDER BY total_encounters DESC;
    """,
    "Readmission by Discharge Disposition (Top 10)": """
        SELECT
            COALESCE(discharge_disposition_id_desc, 'Discharge ' || CAST(discharge_disposition_id AS TEXT)) AS discharge_disposition,
            COUNT(*) AS total_encounters,
            SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_count,
            ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
        FROM encounters
        GROUP BY discharge_disposition
        ORDER BY total_encounters DESC
        LIMIT 10;
    """,
    "Readmission by Prior Inpatient Visits": """
        SELECT
            CASE
                WHEN number_inpatient = 0 THEN '0 visits'
                WHEN number_inpatient = 1 THEN '1 visit'
                WHEN number_inpatient = 2 THEN '2 visits'
                ELSE '3+ visits'
            END AS prior_inpatient_tier,
            COUNT(*) AS total_encounters,
            SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_count,
            ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
        FROM encounters
        GROUP BY prior_inpatient_tier
        ORDER BY MIN(number_inpatient);
    """,
    "Readmission by Clinical Diagnosis Group": """
        SELECT
            COALESCE(diag_1_group, 'Unknown') AS diagnosis_group,
            COUNT(*) AS total_encounters,
            SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_count,
            ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
        FROM encounters
        GROUP BY diag_1_group
        ORDER BY total_encounters DESC;
    """,
    "Readmission by Emergency Utilization": """
        SELECT
            CASE
                WHEN number_emergency = 0 THEN '0 ER visits'
                WHEN number_emergency = 1 THEN '1 ER visit'
                ELSE '2+ ER visits'
            END AS emergency_tier,
            COUNT(*) AS total_encounters,
            SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_count,
            ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
        FROM encounters
        GROUP BY emergency_tier
        ORDER BY MIN(number_emergency);
    """,
    "Readmission by HbA1c Status": """
        SELECT
            COALESCE(A1Cresult, 'Not Measured') AS a1c_status,
            COUNT(*) AS total_encounters,
            SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_count,
            ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
        FROM encounters
        GROUP BY A1Cresult
        ORDER BY total_encounters DESC;
    """,
}


class SQLAnalyticsService:
    """Provides high-level analytical querying and security validation."""

    DESTRUCTIVE_PATTERN = re.compile(
        r"\b(DROP|DELETE|TRUNCATE|ALTER|UPDATE|INSERT|REPLACE|ATTACH|DETACH|VACUUM)\b",
        re.IGNORECASE,
    )

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_overview_metrics(self) -> dict[str, Any]:
        """Calculates headline summary metrics via SQL."""
        df = self.db.execute_query(PREDEFINED_QUERIES["Overview Summary"])
        if df.empty:
            return {
                "total_encounters": 0,
                "unique_patients": 0,
                "readmitted_30d_count": 0,
                "readmission_rate_pct": 0.0,
            }
        row = df.iloc[0]
        return {
            "total_encounters": int(row["total_encounters"]),
            "unique_patients": int(row["unique_patients"]) if pd.notna(row["unique_patients"]) else None,
            "readmitted_30d_count": int(row["readmitted_30d_count"]),
            "readmission_rate_pct": float(row["readmission_rate_pct"]),
        }

    def get_rate_by_dimension(self, dimension_col: str, limit: int = 20) -> pd.DataFrame:
        """Executes a parameterized aggregation for readmission rate by a specific dimension."""
        # Sanitize dimension column name to prevent injection
        if not re.match(r"^[a-zA-Z0-9_]+$", dimension_col):
            raise ValueError(f"Invalid dimension column name: {dimension_col}")

        query = f"""
            SELECT
                COALESCE(CAST({dimension_col} AS TEXT), 'Missing') AS {dimension_col},
                COUNT(*) AS total_encounters,
                SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_count,
                ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
            FROM encounters
            GROUP BY {dimension_col}
            ORDER BY total_encounters DESC
            LIMIT {int(limit)};
        """
        return self.db.execute_query(query)

    def run_predefined_query(self, query_name: str) -> pd.DataFrame:
        """Executes a verified named query from PREDEFINED_QUERIES."""
        if query_name not in PREDEFINED_QUERIES:
            raise KeyError(f"Unknown predefined query: {query_name}. Available: {list(PREDEFINED_QUERIES.keys())}")
        return self.db.execute_query(PREDEFINED_QUERIES[query_name])

    def run_custom_query(self, sql_query: str) -> pd.DataFrame:
        """Validates query against destructive commands and executes read-only SQL.

        Raises:
            PermissionError: If query contains destructive statements (DROP, DELETE, etc.).
        """
        cleaned_sql = sql_query.strip()
        if self.DESTRUCTIVE_PATTERN.search(cleaned_sql):
            raise PermissionError(
                "Destructive operations (DROP, DELETE, TRUNCATE, ALTER, UPDATE, INSERT) "
                "are prohibited in the interactive SQL explorer."
            )

        # Ensure query begins with SELECT or WITH
        first_word = cleaned_sql.split()[0].upper() if cleaned_sql.split() else ""
        if first_word not in ("SELECT", "WITH", "EXPLAIN"):
            raise PermissionError("Only read-only SELECT or WITH statements are allowed.")

        return self.db.execute_query(cleaned_sql)
