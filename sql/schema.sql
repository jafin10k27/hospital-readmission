-- Schema definition for Hospital Readmission SQLite Database

CREATE TABLE IF NOT EXISTS encounters (
    encounter_id INTEGER PRIMARY KEY,
    patient_nbr INTEGER,
    race TEXT,
    gender TEXT,
    age TEXT,
    admission_type_id INTEGER,
    admission_type_id_desc TEXT,
    discharge_disposition_id INTEGER,
    discharge_disposition_id_desc TEXT,
    admission_source_id INTEGER,
    admission_source_id_desc TEXT,
    time_in_hospital INTEGER,
    payer_code TEXT,
    medical_specialty TEXT,
    num_lab_procedures INTEGER,
    num_procedures INTEGER,
    num_medications INTEGER,
    number_outpatient INTEGER,
    number_emergency INTEGER,
    number_inpatient INTEGER,
    diag_1 TEXT,
    diag_1_group TEXT,
    diag_2 TEXT,
    diag_3 TEXT,
    number_diagnoses INTEGER,
    max_glu_serum TEXT,
    A1Cresult TEXT,
    metformin TEXT,
    repaglinide TEXT,
    nateglinide TEXT,
    chlorpropamide TEXT,
    glimepiride TEXT,
    acetohexamide TEXT,
    glipizide TEXT,
    glyburide TEXT,
    tolbutamide TEXT,
    pioglitazone TEXT,
    rosiglitazone TEXT,
    acarbose TEXT,
    miglitol TEXT,
    troglitazone TEXT,
    tolazamide TEXT,
    examide TEXT,
    citoglipton TEXT,
    insulin TEXT,
    glyburide_metformin TEXT,
    glipizide_metformin TEXT,
    glimepiride_pioglitazone TEXT,
    metformin_rosiglitazone TEXT,
    metformin_pioglitazone TEXT,
    change TEXT,
    diabetesMed TEXT,
    readmitted TEXT,
    readmitted_30d INTEGER
);

CREATE INDEX IF NOT EXISTS idx_encounters_patient ON encounters(patient_nbr);
CREATE INDEX IF NOT EXISTS idx_encounters_readmitted_30d ON encounters(readmitted_30d);
CREATE INDEX IF NOT EXISTS idx_encounters_age ON encounters(age);
CREATE INDEX IF NOT EXISTS idx_encounters_admission_type ON encounters(admission_type_id);
CREATE INDEX IF NOT EXISTS idx_encounters_discharge ON encounters(discharge_disposition_id);
CREATE INDEX IF NOT EXISTS idx_encounters_diag1_group ON encounters(diag_1_group);

CREATE TABLE IF NOT EXISTS cleaning_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    operation TEXT NOT NULL,
    target_column TEXT,
    rows_before INTEGER,
    rows_after INTEGER,
    values_affected INTEGER,
    reason TEXT,
    reversible BOOLEAN
);

CREATE TABLE IF NOT EXISTS validation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    severity TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    column_name TEXT,
    affected_rows INTEGER,
    affected_percentage REAL,
    description TEXT,
    recommended_action TEXT
);

CREATE TABLE IF NOT EXISTS data_quality_summary (
    metric_name TEXT PRIMARY KEY,
    metric_value TEXT,
    metric_category TEXT,
    updated_at TEXT
);
