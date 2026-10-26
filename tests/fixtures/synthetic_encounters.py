"""Synthetic Encounter Test Fixtures.

Contains deterministic synthetic healthcare encounter datasets with
explicitly documented expected metrics for automated testing.
NOTICE: This is purely synthetic benchmark data for testing, NOT real clinical records.
"""

from pathlib import Path

import pandas as pd


def create_synthetic_raw_dataframe() -> pd.DataFrame:
    """Creates a deterministic synthetic encounter dataset (10 rows).

    Documented properties:
    - Total rows: 10
    - Exact duplicate rows: 1 (row 0 and row 1 are identical)
    - Unique patients: 7 (patient 101 has 3 encounters, patient 102 has 2 encounters)
    - Outcome distribution:
        - '<30': 3 encounters (rows 0, 1, 4) -> 30-day readmissions
        - '>30': 4 encounters (rows 2, 5, 7, 9)
        - 'NO': 3 encounters (rows 3, 6, 8)
    - Sentinels ('?'):
        - 'race': row 2 has '?'
        - 'weight': 9 rows have '?' (90% missingness)
        - 'payer_code': 8 rows have '?' (80% missingness)
    """
    data = {
        "encounter_id": [1, 1, 3, 4, 5, 6, 7, 8, 9, 10],  # row 0 and 1 duplicate encounter
        "patient_nbr": [101, 101, 101, 102, 102, 103, 104, 105, 106, 107],
        "race": ["Caucasian", "Caucasian", "?", "AfricanAmerican", "Caucasian", "Other", "Caucasian", "Asian", "Caucasian", "Caucasian"],
        "gender": ["Female", "Female", "Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female"],
        "age": ["[70-80)", "[70-80)", "[60-70)", "[50-60)", "[70-80)", "[80-90)", "[60-70)", "[40-50)", "[70-80)", "[60-70)"],
        "weight": ["?", "?", "?", "?", "[75-100)", "?", "?", "?", "?", "?"],
        "admission_type_id": [1, 1, 2, 1, 3, 1, 2, 1, 1, 2],
        "discharge_disposition_id": [1, 1, 3, 1, 1, 6, 1, 1, 3, 1],
        "admission_source_id": [7, 7, 1, 7, 1, 7, 1, 7, 7, 1],
        "time_in_hospital": [3, 3, 5, 2, 4, 8, 1, 6, 2, 4],
        "payer_code": ["?", "?", "MC", "?", "?", "?", "MD", "?", "?", "?"],
        "medical_specialty": ["InternalMedicine", "InternalMedicine", "?", "Cardiology", "?", "?", "Surgery", "?", "?", "InternalMedicine"],
        "num_lab_procedures": [45, 45, 60, 20, 52, 70, 15, 65, 30, 48],
        "num_procedures": [0, 0, 1, 0, 2, 0, 1, 3, 0, 1],
        "num_medications": [12, 12, 18, 8, 22, 14, 6, 25, 10, 15],
        "number_outpatient": [0, 0, 1, 0, 0, 2, 0, 0, 1, 0],
        "number_emergency": [0, 0, 1, 0, 2, 0, 0, 1, 0, 0],
        "number_inpatient": [0, 0, 2, 0, 1, 3, 0, 0, 1, 0],
        "diag_1": ["414", "414", "250.01", "428", "486", "584", "786", "250.02", "410", "491"],
        "diag_2": ["250", "250", "401", "250", "428", "250", "401", "428", "250", "428"],
        "diag_3": ["401", "401", "428", "401", "250", "401", "250", "401", "401", "250"],
        "number_diagnoses": [9, 9, 8, 5, 9, 9, 4, 8, 7, 6],
        "max_glu_serum": ["None", "None", "None", "None", ">300", "None", "Norm", "None", "None", "None"],
        "A1Cresult": ["None", "None", ">8", "None", "Norm", "None", "None", ">7", "None", "None"],
        "metformin": ["No", "No", "No", "No", "Steady", "No", "Steady", "No", "No", "Steady"],
        "repaglinide": ["No"] * 10,
        "nateglinide": ["No"] * 10,
        "chlorpropamide": ["No"] * 10,
        "glimepiride": ["No"] * 10,
        "acetohexamide": ["No"] * 10,
        "glipizide": ["No"] * 10,
        "glyburide": ["No"] * 10,
        "tolbutamide": ["No"] * 10,
        "pioglitazone": ["No"] * 10,
        "rosiglitazone": ["No"] * 10,
        "acarbose": ["No"] * 10,
        "miglitol": ["No"] * 10,
        "troglitazone": ["No"] * 10,
        "tolazamide": ["No"] * 10,
        "examide": ["No"] * 10,
        "citoglipton": ["No"] * 10,
        "insulin": ["No", "No", "Up", "Steady", "Down", "Steady", "No", "Up", "No", "Steady"],
        "glyburide-metformin": ["No"] * 10,
        "glipizide-metformin": ["No"] * 10,
        "glimepiride-pioglitazone": ["No"] * 10,
        "metformin-rosiglitazone": ["No"] * 10,
        "metformin-pioglitazone": ["No"] * 10,
        "change": ["No", "No", "Ch", "Ch", "Ch", "Ch", "No", "Ch", "No", "Ch"],
        "diabetesMed": ["No", "No", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "No", "Yes"],
        "readmitted": ["<30", "<30", ">30", "NO", "<30", ">30", "NO", ">30", "NO", ">30"],
    }
    return pd.DataFrame(data)


def save_synthetic_csv(path: Path | str) -> Path:
    """Saves the synthetic fixture to a CSV file."""
    df = create_synthetic_raw_dataframe()
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=False)
    return file_path
