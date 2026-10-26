-- Analytical Queries for Hospital Readmission Analysis

-- 1. Total Encounters & Unique Patients Summary
SELECT
    COUNT(*) AS total_encounters,
    COUNT(DISTINCT patient_nbr) AS unique_patients,
    ROUND(CAST(COUNT(*) AS REAL) / NULLIF(COUNT(DISTINCT patient_nbr), 0), 2) AS encounters_per_patient,
    SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_30d_count,
    ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
FROM encounters;

-- 2. Readmission Rate by Age Group
SELECT
    COALESCE(age, 'Unknown') AS age_group,
    COUNT(*) AS encounter_count,
    SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_count,
    ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
FROM encounters
GROUP BY age
ORDER BY age;

-- 3. Readmission Rate by Admission Type
SELECT
    COALESCE(admission_type_id_desc, 'Type ' || CAST(admission_type_id AS TEXT)) AS admission_type,
    COUNT(*) AS encounter_count,
    SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_count,
    ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
FROM encounters
GROUP BY admission_type
ORDER BY encounter_count DESC;

-- 4. Readmission Rate by Discharge Disposition
SELECT
    COALESCE(discharge_disposition_id_desc, 'Discharge ' || CAST(discharge_disposition_id AS TEXT)) AS discharge_disposition,
    COUNT(*) AS encounter_count,
    SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_count,
    ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
FROM encounters
GROUP BY discharge_disposition
ORDER BY encounter_count DESC
LIMIT 15;

-- 5. Readmission Rate by Prior Inpatient Visits
SELECT
    CASE
        WHEN number_inpatient = 0 THEN '0 visits'
        WHEN number_inpatient = 1 THEN '1 visit'
        WHEN number_inpatient = 2 THEN '2 visits'
        ELSE '3+ visits'
    END AS prior_inpatient_tier,
    COUNT(*) AS encounter_count,
    SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_count,
    ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
FROM encounters
GROUP BY prior_inpatient_tier
ORDER BY MIN(number_inpatient);

-- 6. Readmission Rate by Primary Clinical Diagnosis Group
SELECT
    COALESCE(diag_1_group, 'Unknown') AS diagnosis_group,
    COUNT(*) AS encounter_count,
    SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_count,
    ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
FROM encounters
GROUP BY diag_1_group
ORDER BY encounter_count DESC;

-- 7. Readmission Rate by HbA1c Result
SELECT
    COALESCE(A1Cresult, 'None') AS a1c_result,
    COUNT(*) AS encounter_count,
    SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_count,
    ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
FROM encounters
GROUP BY A1Cresult
ORDER BY encounter_count DESC;

-- 8. Readmission Rate by Medication Change Status
SELECT
    COALESCE(change, 'No') AS medication_change,
    COUNT(*) AS encounter_count,
    SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmitted_count,
    ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
FROM encounters
GROUP BY change
ORDER BY encounter_count DESC;
