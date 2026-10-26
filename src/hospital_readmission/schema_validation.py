"""Schema and Data Validation Module (FR-2).

Performs comprehensive validation of healthcare encounter records including:
- Missingness audits
- Exact duplicate rows vs. repeated patient encounters
- Unexpected data types and out-of-range numericals
- Suspicious/sentinel values
- Constant or empty columns
- Categorical domain validity
- Structured validation report with severity ratings and remediation guidance.
"""

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

import pandas as pd

from hospital_readmission.logging_config import setup_logger

logger = setup_logger(__name__)


class Severity(StrEnum):
    """Validation issue severity levels."""
    ERROR = "ERROR"       # Blocks critical analytics or corrupts definitions
    WARNING = "WARNING"   # Potential data quality issue requiring caution or cleaning
    INFO = "INFO"         # Informational metric (e.g. repeated encounters)


@dataclass
class ValidationIssue:
    """Represents a specific validation finding."""

    issue_type: str
    severity: Severity
    column: str | None
    affected_rows: int
    affected_percentage: float
    description: str
    recommended_action: str

    def to_dict(self) -> dict[str, Any]:
        res = asdict(self)
        res["severity"] = self.severity.value
        return res


@dataclass
class ValidationReport:
    """Comprehensive validation report for an ingested dataset."""

    total_rows: int
    total_columns: int
    exact_duplicates: int
    unique_encounters: int | None
    unique_patients: int | None
    issues: list[ValidationIssue]

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.INFO)

    def to_dataframe(self) -> pd.DataFrame:
        """Converts issues into a formatted pandas DataFrame."""
        if not self.issues:
            return pd.DataFrame(
                columns=[
                    "severity",
                    "issue_type",
                    "column",
                    "affected_rows",
                    "affected_percentage",
                    "description",
                    "recommended_action",
                ]
            )
        data = [i.to_dict() for i in self.issues]
        return pd.DataFrame(data)


class DataValidator:
    """Validates dataframe against expected schema, integrity rules, and healthcare constraints."""

    def __init__(
        self,
        schema: dict[str, Any] | None = None,
        sentinel_values: list[str] | None = None,
    ):
        self.schema = schema or {}
        self.sentinel_values = sentinel_values or ["?", "None", "NULL", "Unknown/Invalid"]

    def validate(self, df: pd.DataFrame) -> ValidationReport:
        """Runs the complete suite of validation checks on the given DataFrame.

        Args:
            df: Input raw or uncleaned DataFrame.

        Returns:
            ValidationReport containing detected issues and dataset dimension metrics.
        """
        logger.info("Starting schema and data quality validation...")
        issues: list[ValidationIssue] = []
        n_rows = len(df)
        n_cols = len(df.columns)

        if n_rows == 0:
            issues.append(
                ValidationIssue(
                    issue_type="empty_dataset",
                    severity=Severity.ERROR,
                    column=None,
                    affected_rows=0,
                    affected_percentage=0.0,
                    description="The dataset contains zero records.",
                    recommended_action="Ensure the source file contains valid encounter data.",
                )
            )
            return ValidationReport(0, n_cols, 0, None, None, issues)

        # 1. Exact Duplicate Rows
        exact_dups = int(df.duplicated().sum())
        if exact_dups > 0:
            pct = round((exact_dups / n_rows) * 100, 2)
            issues.append(
                ValidationIssue(
                    issue_type="exact_duplicate_rows",
                    severity=Severity.WARNING,
                    column=None,
                    affected_rows=exact_dups,
                    affected_percentage=pct,
                    description=f"Found {exact_dups} ({pct}%) exact duplicate row(s) identical across all columns.",
                    recommended_action="Deduplicate exact matching rows during the cleaning phase.",
                )
            )

        # 2. Encounter and Patient Identifiers
        encounter_col = self.schema.get("encounter_id", "encounter_id")
        unique_encounters = None
        if encounter_col in df.columns:
            unique_encounters = int(df[encounter_col].nunique())
            dup_encounters = n_rows - unique_encounters
            if dup_encounters > 0:
                pct = round((dup_encounters / n_rows) * 100, 2)
                issues.append(
                    ValidationIssue(
                        issue_type="duplicate_encounter_id",
                        severity=Severity.ERROR,
                        column=encounter_col,
                        affected_rows=dup_encounters,
                        affected_percentage=pct,
                        description=(
                            f"Encounter ID '{encounter_col}' is expected to be unique per encounter, "
                            f"but {dup_encounters} duplicated occurrences were identified."
                        ),
                        recommended_action="Investigate source data pipeline; encounter IDs should be primary keys.",
                    )
                )

        patient_col = self.schema.get("patient_id", "patient_nbr")
        unique_patients = None
        if patient_col in df.columns:
            unique_patients = int(df[patient_col].nunique())
            repeated_patients = n_rows - unique_patients
            if repeated_patients > 0:
                pct = round((repeated_patients / n_rows) * 100, 2)
                issues.append(
                    ValidationIssue(
                        issue_type="multiple_patient_encounters",
                        severity=Severity.INFO,
                        column=patient_col,
                        affected_rows=repeated_patients,
                        affected_percentage=pct,
                        description=(
                            f"Identified {repeated_patients} encounters belonging to patients with multiple admissions "
                            f"({unique_patients} unique patients across {n_rows} encounters)."
                        ),
                        recommended_action=(
                            "Distinguish exact duplicate rows from multiple longitudinal encounters. "
                            "Do not delete patient encounters simply because they share a patient ID."
                        ),
                    )
                )

        # 3. Missingness & Sentinel Value Audit
        for col in df.columns:
            col_series = df[col]
            # Standard nulls
            standard_nulls = col_series.isna().sum()

            # Sentinel nulls (e.g. '?', 'None')
            sentinel_count = 0
            if col_series.dtype == object or isinstance(col_series.dtype, pd.StringDtype):
                str_vals = col_series.astype(str).str.strip()
                sentinel_mask = str_vals.isin(self.sentinel_values)
                sentinel_count = int(sentinel_mask.sum())

            total_missing = int(standard_nulls + sentinel_count)
            if total_missing > 0:
                pct = round((total_missing / n_rows) * 100, 2)
                severity = Severity.WARNING if pct > 30 else Severity.INFO
                if pct == 100:
                    severity = Severity.ERROR
                    issues.append(
                        ValidationIssue(
                            issue_type="empty_column",
                            severity=severity,
                            column=col,
                            affected_rows=total_missing,
                            affected_percentage=pct,
                            description=f"Column '{col}' is completely empty (100% missing values).",
                            recommended_action=f"Drop uninformative column '{col}' during cleaning.",
                        )
                    )
                elif pct > 50:
                    issues.append(
                        ValidationIssue(
                            issue_type="high_missingness",
                            severity=severity,
                            column=col,
                            affected_rows=total_missing,
                            affected_percentage=pct,
                            description=(
                                f"Column '{col}' has severe missingness: {total_missing} ({pct}%) values "
                                f"are null or sentinel markers ({self.sentinel_values})."
                            ),
                            recommended_action=f"Evaluate whether '{col}' has enough coverage for valid statistical inference.",
                        )
                    )

        # 4. Constant Columns (Zero Variance)
        for col in df.columns:
            non_null = df[col].dropna()
            # Also exclude sentinels when checking constantness
            if non_null.dtype == object:
                non_null = non_null[~non_null.astype(str).str.strip().isin(self.sentinel_values)]
            if len(non_null) > 0 and non_null.nunique() == 1:
                val = non_null.iloc[0]
                issues.append(
                    ValidationIssue(
                        issue_type="constant_column",
                        severity=Severity.WARNING,
                        column=col,
                        affected_rows=n_rows,
                        affected_percentage=100.0,
                        description=f"Column '{col}' is invariant, containing only single value: '{val}'.",
                        recommended_action=f"Exclude '{col}' from bivariate and multivariable association tests.",
                    )
                )

        # 5. Outcome Column Validation
        outcome_col = self.schema.get("outcome_column", "readmitted")
        if outcome_col not in df.columns:
            issues.append(
                ValidationIssue(
                    issue_type="missing_outcome_column",
                    severity=Severity.ERROR,
                    column=outcome_col,
                    affected_rows=n_rows,
                    affected_percentage=100.0,
                    description=f"Outcome column '{outcome_col}' was not found in the dataset.",
                    recommended_action="Ensure dataset schema aligns with the expected readmission outcome column.",
                )
            )
        else:
            valid_outcomes = {"<30", ">30", "NO"}
            actual_outcomes = set(df[outcome_col].dropna().astype(str).str.strip().unique())
            invalid_outcomes = actual_outcomes - valid_outcomes
            if invalid_outcomes:
                invalid_count = int(
                    df[outcome_col].astype(str).str.strip().isin(invalid_outcomes).sum()
                )
                pct = round((invalid_count / n_rows) * 100, 2)
                issues.append(
                    ValidationIssue(
                        issue_type="invalid_outcome_labels",
                        severity=Severity.ERROR,
                        column=outcome_col,
                        affected_rows=invalid_count,
                        affected_percentage=pct,
                        description=(
                            f"Outcome column contains unrecognized labels {invalid_outcomes}. "
                            f"Expected labels: {valid_outcomes}."
                        ),
                        recommended_action="Remap or filter out invalid outcome values before outcome binarization.",
                    )
                )

        # 6. Numerical Value Range Checks
        num_ranges = self.schema.get("numerical_ranges", {})
        for col, (min_val, max_val) in num_ranges.items():
            if col in df.columns:
                series_numeric = pd.to_numeric(df[col], errors="coerce")
                out_of_bounds = series_numeric.dropna()[
                    (series_numeric.dropna() < min_val) | (series_numeric.dropna() > max_val)
                ]
                if len(out_of_bounds) > 0:
                    pct = round((len(out_of_bounds) / n_rows) * 100, 2)
                    issues.append(
                        ValidationIssue(
                            issue_type="out_of_range_numerical",
                            severity=Severity.WARNING,
                            column=col,
                            affected_rows=len(out_of_bounds),
                            affected_percentage=pct,
                            description=(
                                f"Column '{col}' has {len(out_of_bounds)} ({pct}%) values outside "
                                f"clinical expected bounds [{min_val}, {max_val}]. "
                                f"Observed range: [{series_numeric.min()}, {series_numeric.max()}]."
                            ),
                            recommended_action=f"Inspect outliers in '{col}' for data entry anomalies.",
                        )
                    )

        # 7. Categorical Domain Checks
        gender_col = "gender"
        if gender_col in df.columns:
            valid_genders = set(self.schema.get("valid_gender_values", ["Female", "Male", "Unknown/Invalid"]))
            actual_genders = set(df[gender_col].dropna().astype(str).str.strip().unique())
            invalid_g = actual_genders - valid_genders
            if invalid_g:
                count = int(df[gender_col].astype(str).str.strip().isin(invalid_g).sum())
                pct = round((count / n_rows) * 100, 2)
                issues.append(
                    ValidationIssue(
                        issue_type="invalid_gender_values",
                        severity=Severity.WARNING,
                        column=gender_col,
                        affected_rows=count,
                        affected_percentage=pct,
                        description=f"Column 'gender' has unexpected categorical values: {invalid_g}.",
                        recommended_action="Map unstandardized gender values to 'Unknown/Invalid' or NaN.",
                    )
                )

        logger.info(
            "Validation finished: %d issues identified (%d ERROR, %d WARNING, %d INFO)",
            len(issues),
            sum(1 for i in issues if i.severity == Severity.ERROR),
            sum(1 for i in issues if i.severity == Severity.WARNING),
            sum(1 for i in issues if i.severity == Severity.INFO),
        )

        return ValidationReport(
            total_rows=n_rows,
            total_columns=n_cols,
            exact_duplicates=exact_dups,
            unique_encounters=unique_encounters,
            unique_patients=unique_patients,
            issues=issues,
        )
