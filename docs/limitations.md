# Methodological Limitations & Research Context

Understanding the boundaries of observational healthcare data is essential for responsible clinical analytics. This document details the methodological limitations, potential biases, and non-causal constraints of the Hospital Readmission Intelligence Platform.

---

## 1. Non-Causality and Confounding

### 1.1 Observational vs. Interventional Inference
The findings produced by this platform represent retrospective observational associations. **Statistical association does not establish biological or clinical causation.** 
- An elevated readmission rate in a subgroup (e.g. patients prescribed insulin or with prior inpatient encounters) reflects baseline disease severity, chronic disease duration, or care transition complexities rather than an adverse effect of the medication or hospital care itself.
- Clinicians must never modify pharmacotherapy or discharge planning based solely on unadjusted bivariate associations.

### 1.2 Unmeasured Confounders
Administrative and encounter datasets omit vital determinants of hospital readmission:
- **Social Determinants of Health (SDOH):** Housing instability, food insecurity, economic strain, transportation barriers, and health literacy are not captured.
- **Medication Adherence Post-Discharge:** Whether patients filled outpatient prescriptions or adhered to titration schedules is unrecorded.
- **Outpatient Care Coordination:** Post-discharge primary care follow-up within 7–14 days is a critical factor unmeasured in this encounter record.
- **Functional Status & Cognitive Impairment:** ADL/IADL independence and baseline cognitive impairment are major unmeasured predictors in geriatric populations.

---

## 2. Dataset Censoring & Information Bias

### 2.1 Out-of-Network Readmissions (Right Censoring)
The dataset comprises encounters across 130 hospitals within participating health systems. 
- If a discharged patient was readmitted to a non-participating community hospital, VA medical center, or out-of-state facility within 30 days, that encounter is recorded as `NO` readmission.
- This creates **informative right-censoring** and potentially underestimates true population 30-day readmission incidence.

### 2.2 Time Frame (1999–2008)
- Clinical practice guidelines for glycemic management, hospitalist models, bundled payments, and transition-of-care programs have evolved substantially since 2008.
- Contemporary readmission rates in modern electronic health record (EHR) systems may differ from historic cohorts.

---

## 3. High Missingness in Clinical Features

- Certain variables in the original UCI dataset (e.g., `weight` at 96.8% missing, `payer_code` at 52% missing, `medical_specialty` at 49% missing) could not support robust inference and were dropped or retained as unassigned.
- Glycated hemoglobin (`A1Cresult`) was not recorded in approximately 83% of encounters, indicating selective testing based on physician suspicion or protocol rather than universal screening.

---

## 4. Model Interpretation Warnings

- **Exploratory Hypothesis Generation:** All tests, tables, and charts are intended strictly for exploratory research and operational hypothesis generation.
- **No Diagnostic or Prognostic Claim:** This platform does not serve as a clinical decision support system, software as a medical device (SaMD), or individual patient triage device.
