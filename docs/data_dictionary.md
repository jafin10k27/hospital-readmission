# Healthcare Encounter Data Dictionary

This document details all 50 clinical and administrative attributes present in the Diabetes 130-US Hospitals (1999–2008) dataset (UCI Machine Learning Repository / Strack et al., 2014).

---

## 1. Identifiers & Demographics

| Column Name | Inferred Type | Clinical / Operational Definition | Expected Values / Examples | Missingness Handling |
| :--- | :--- | :--- | :--- | :--- |
| `encounter_id` | Integer (Primary Key) | Unique identifier representing a discrete hospital admission episode. | E.g. `2278392` | Cannot be null. |
| `patient_nbr` | Integer | Unique identifier representing an individual patient across repeated visits. | E.g. `8222157` | Longitudinal tracking; preserved during patient-level deduplication. |
| `race` | Categorical | Self-reported racial classification of the patient. | `Caucasian`, `AfricanAmerican`, `Hispanic`, `Asian`, `Other`, `?` | Replaced `?` with `NaN` (~2.2% missing). |
| `gender` | Categorical | Biological sex recorded at admission. | `Female`, `Male`, `Unknown/Invalid` | Validated; non-standard entries flagged. |
| `age` | Categorical | 10-year aggregated age bracket at encounter start. | `[0-10)`, `[10-20)`, ..., `[90-100)` | Standardized categorical intervals. |
| `weight` | Categorical | Patient body weight measured in pounds bracketed in 25-lb intervals. | `[0-25)`, `[25-50)`, `?` | Extreme missingness (>96%); dropped in sparse column cleaner. |

---

## 2. Admission & Discharge Logistics

| Column Name | Inferred Type | Clinical / Operational Definition | Expected Values / Examples | Mapped Descriptor |
| :--- | :--- | :--- | :--- | :--- |
| `admission_type_id` | Integer | Urgency classification at time of hospital admission. | `1`=Emergency, `2`=Urgent, `3`=Elective, `4`=Newborn, `5`=Not Available, `7`=Trauma Center | `admission_type_id_desc` |
| `discharge_disposition_id` | Integer | Destination and clinical status at discharge. | `1`=Discharged to home, `2`=Transfer to acute hospital, `3`=SNF, `6`=Home with home health, `11`=Expired | `discharge_disposition_id_desc` |
| `admission_source_id` | Integer | Origin of encounter referral. | `1`=Physician Referral, `7`=Emergency Room, `2`=Clinic Referral | `admission_source_id_desc` |
| `time_in_hospital` | Integer | Total length of stay (LOS) recorded in integer days. | Range: `1` to `14` days. | Continuous numeric attribute. |
| `payer_code` | Categorical | Primary health plan / insurance payer. | `MC` (Medicare), `MD` (Medicaid), `BC` (Blue Cross), `?` | High missingness (>50% `?`); dropped. |
| `medical_specialty` | Categorical | Specialty of admitting physician. | `InternalMedicine`, `Cardiology`, `Surgery-General`, `?` | Frequent `?` (~49% missing); retained as unassigned. |

---

## 3. Clinical Intensity & Diagnostic Attributes

| Column Name | Inferred Type | Clinical / Operational Definition | Expected Values / Range | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `num_lab_procedures` | Integer | Count of discrete diagnostic lab tests performed during stay. | Range: `1` to `132` | Metric of diagnostic intensity. |
| `num_procedures` | Integer | Count of non-lab medical/surgical interventions performed. | Range: `0` to `6` | Surgical procedure burden. |
| `num_medications` | Integer | Total number of distinct therapeutic medications administered. | Range: `1` to `81` | Pharmacotherapy complexity. |
| `number_outpatient` | Integer | Number of recorded outpatient visits in previous 12 months. | Range: `0` to `42` | Pre-encounter ambulatory utilization. |
| `number_emergency` | Integer | Number of emergency department visits in previous 12 months. | Range: `0` to `76` | Pre-encounter acute utilization. |
| `number_inpatient` | Integer | Number of acute inpatient admissions in previous 12 months. | Range: `0` to `21` | Heavy predictor of readmission propensity. |
| `diag_1` | Categorical / String | Primary ICD-9 diagnosis code describing chief cause of admission. | E.g. `250.01`, `414`, `428` | Clustered into `diag_1_group`. |
| `diag_1_group` | Categorical | High-level clinical disease taxonomy. | `Circulatory`, `Respiratory`, `Digestive`, `Diabetes`, `Injury`, `Genitourinary`, `Musculoskeletal`, `Neoplasms`, `Other` | Generated during cleaning. |
| `diag_2` | Categorical / String | Secondary concurrent ICD-9 diagnosis code. | E.g. `401.9`, `250` | Comorbidity burden. |
| `diag_3` | Categorical / String | Tertiary concurrent ICD-9 diagnosis code. | E.g. `428.0` | Secondary comorbidity. |
| `number_diagnoses` | Integer | Total count of diagnoses coded on hospital billing record. | Range: `1` to `16` | Multimorbidity index. |

---

## 4. Glycemic Control & Diabetic Pharmacotherapy

| Column Name | Inferred Type | Definition | Permitted Values |
| :--- | :--- | :--- | :--- |
| `max_glu_serum` | Categorical | Maximum serum glucose lab result. | `>200`, `>300`, `Norm`, `None` (not measured) |
| `A1Cresult` | Categorical | Glycated hemoglobin (HbA1c) lab test result. | `>8` (high), `>7` (elevated), `Norm`, `None` (not measured) |
| `metformin` | Categorical | Biguanide antihyperglycemic medication status. | `No`, `Steady`, `Up`, `Down` |
| `repaglinide` | Categorical | Meglitinide analog. | `No`, `Steady`, `Up`, `Down` |
| `nateglinide` | Categorical | D-phenylalanine derivative. | `No`, `Steady`, `Up`, `Down` |
| `chlorpropamide` | Categorical | First-generation sulfonylurea. | `No`, `Steady`, `Up`, `Down` |
| `glimepiride` | Categorical | Second-generation sulfonylurea. | `No`, `Steady`, `Up`, `Down` |
| `acetohexamide` | Categorical | First-generation sulfonylurea. | `No`, `Steady` |
| `glipizide` | Categorical | Second-generation sulfonylurea. | `No`, `Steady`, `Up`, `Down` |
| `glyburide` | Categorical | Second-generation sulfonylurea. | `No`, `Steady`, `Up`, `Down` |
| `tolbutamide` | Categorical | First-generation sulfonylurea. | `No`, `Steady`, `Up` |
| `pioglitazone` | Categorical | Thiazolidinedione (TZD). | `No`, `Steady`, `Up`, `Down` |
| `rosiglitazone` | Categorical | Thiazolidinedione (TZD). | `No`, `Steady`, `Up`, `Down` |
| `acarbose` | Categorical | Alpha-glucosidase inhibitor. | `No`, `Steady`, `Up`, `Down` |
| `miglitol` | Categorical | Alpha-glucosidase inhibitor. | `No`, `Steady`, `Up`, `Down` |
| `troglitazone` | Categorical | Thiazolidinedione (TZD). | `No`, `Steady` |
| `tolazamide` | Categorical | First-generation sulfonylurea. | `No`, `Steady`, `Up` |
| `examide` | Categorical | Incretin mimetic. | Invariant (`No`) |
| `citoglipton` | Categorical | DPP-4 inhibitor. | Invariant (`No`) |
| `insulin` | Categorical | Exogenous insulin therapy status. | `No`, `Steady`, `Up`, `Down` |
| `glyburide-metformin` | Categorical | Fixed-dose combination. | `No`, `Steady`, `Up`, `Down` |
| `glipizide-metformin` | Categorical | Fixed-dose combination. | `No`, `Steady` |
| `glimepiride-pioglitazone` | Categorical | Fixed-dose combination. | `No`, `Steady` |
| `metformin-rosiglitazone` | Categorical | Fixed-dose combination. | Invariant (`No`) |
| `metformin-pioglitazone` | Categorical | Fixed-dose combination. | `No`, `Steady` |
| `change` | Categorical | Indicates whether diabetes pharmacotherapy was altered. | `Ch` (Yes, medication changed), `No` |
| `diabetesMed` | Categorical | Indicates whether any diabetic medication was prescribed. | `Yes`, `No` |

---

## 5. Outcome Variables

| Column Name | Inferred Type | Definition | Values & Binarization |
| :--- | :--- | :--- | :--- |
| `readmitted` | Categorical (Raw) | Raw hospital encounter readmission status. | `<30` (readmitted within 30 days), `>30` (readmitted after 30 days), `NO` (no recorded readmission). |
| `readmitted_30d` | Binary Integer (Engineered) | Primary endpoint: 30-day hospital readmission indicator. | `1` = Readmitted within 30 days (`<30`), `0` = Not readmitted within 30 days (`>30` or `NO`). |
