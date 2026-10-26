# Analytical & Engineering Methodology

This document outlines the architectural principles, data quality assessment algorithms, statistical methods, and SQL data modeling employed in the Hospital Readmission Intelligence Platform.

---

## 1. Pipeline Architecture & Workflow

```
[ Raw CSV Files ]
       │
       ▼
[ Data Ingestion Engine (FR-1) ]
  • File existence, non-emptiness, format validation
  • Encoding fallback (utf-8 → latin-1 → iso-8859-1 → cp1252)
  • Ingestion metadata recording (timestamp, size, dtypes)
       │
       ▼
[ Schema & Data Quality Validation Engine (FR-2) ]
  • Exact duplicate row detection
  • Identifier audits (encounter_id uniqueness vs. patient_nbr longitudinal visits)
  • Missingness and sentinel marker discovery ('?', 'None', 'NULL')
  • Constant/zero-variance column flagging
  • Categorical domain and numerical range checks
       │
       ▼
[ Auditable Data Cleaning Pipeline (FR-3) ]
  • Reversible/irreversible transformation logging
  • Sentinel to NaN normalization
  • Exact duplicate removal
  • Sparse column elimination (e.g. weight > 96% missing)
  • Clinical ID descriptor joins (admission_type, discharge_disposition)
  • ICD-9 primary diagnosis clinical grouping (Circulatory, Respiratory, Diabetes, etc.)
       │
       ▼
[ Readmission Outcome Binarization (FR-5) ]
  • Label isolation: '<30' → 1, '>30' / 'NO' → 0
  • Raw outcome preservation
       │
       ▼
[ SQLite Relational Analytics Store (FR-4) ]
  • Parametric table ingestion (`encounters`, `cleaning_log`, `validation_log`)
  • B-tree indexing on frequent filter attributes (patient_nbr, readmitted_30d, age)
  • Safe, read-only SQL query execution service with AST/regex command filtering
       │
       ▼
[ Statistical Inference & Exploratory Analytics (FR-6, FR-7) ]
  • Wilson score binomial confidence intervals
  • Contingency table Chi-Square tests of independence with Cramer's V effect sizes
  • Non-parametric Mann-Whitney U rank-sum tests with rank-biserial correlations
  • Benjamini-Hochberg False Discovery Rate (FDR) multiple-testing correction
       │
       ▼
[ Interactive Streamlit Dashboard & Reports (FR-8, FR-9, FR-10, FR-11) ]
  • Responsive Plotly charts with error bars and sample denominators
  • Curated and custom SQL query runners
  • Automated Jinja2 HTML dossiers and ReportLab PDF document compilation
```

---

## 2. Statistical Methodology

### 2.1 Binomial Proportions & Wilson Score Confidence Intervals
When reporting readmission rates $\hat{p} = \frac{k}{n}$, standard normal approximation (Wald intervals $\hat{p} \pm z\sqrt{\hat{p}(1-\hat{p})/n}$) suffers from severe coverage errors when sample sizes are small or readmission rates deviate from 0.5.

The platform utilizes the **Wilson Score Interval with Continuity Correction**:

$$\tilde{p} = \frac{k + \frac{z^2}{2}}{n + z^2}$$

$$\text{CI}_{95\%} = \tilde{p} \pm \frac{z}{n + z^2} \sqrt{\frac{k(n-k)}{n} + \frac{z^2}{4}}$$

where $z = 1.95996$ for a two-tailed $\alpha = 0.05$. Wilson intervals guarantee strictly non-negative bounds and proper coverage probability.

### 2.2 Categorical Association & Effect Sizes
For categorical attributes (e.g. age cohort, admission type, primary diagnosis group), the null hypothesis $H_0$ posits independence between the categorical attribute and 30-day readmission status.
- **Test:** Pearson's $\chi^2$ test of independence:
  $$\chi^2 = \sum \frac{(O_{ij} - E_{ij})^2}{E_{ij}}$$
- **Assumption Verification:** The expected frequency $E_{ij}$ is calculated for every cell. If $\min(E_{ij}) < 5$, a data quality warning is flagged.
- **Effect Size:** Rather than relying exclusively on p-values (which reach statistical significance automatically in large $N > 100,000$ cohorts), we compute **Cramer's V**:
  $$V = \sqrt{\frac{\chi^2}{N \cdot \min(r - 1, c - 1)}}$$
  Categorized as Negligible ($V < 0.10$), Small ($0.10 \le V < 0.30$), Medium ($0.30 \le V < 0.50$), or Large ($V \ge 0.50$).

### 2.3 Non-Parametric Continuous Two-Sample Tests
Continuous hospital encounter metrics (such as prior inpatient visits, prior emergency visits, and length of stay) are heavily right-skewed with significant zero-inflation.
- **Test:** Mann-Whitney U test (Wilcoxon rank-sum test) evaluates stochastic dominance without imposing Gaussian normality assumptions.
- **Effect Size:** Rank-Biserial Correlation ($r_{rb}$):
  $$r_{rb} = 1 - \frac{2U}{n_1 n_2}$$
  bounded between $[-1, +1]$.

### 2.4 Multiple Testing Corrections
Testing multiple clinical biomarkers simultaneously increases family-wise Type I error rates. The platform provides:
1. **Benjamini-Hochberg False Discovery Rate (FDR):** Controls the expected proportion of false positives among rejected null hypotheses:
   $$P_{(i)} \le \frac{i}{m} Q$$
2. **Bonferroni Adjustment:** Conservative family-wise error control:
   $$\alpha_{\text{adjusted}} = \min(1.0, P \cdot m)$$

---

## 3. SQL Data Modeling & Security

### 3.1 Relational Schema & Indexing
The clean encounter dataset is loaded into SQLite:
- `encounters`: Denormalized encounter records with mapped IDs (`admission_type_id_desc`, `discharge_disposition_id_desc`) and engineered binary outcome `readmitted_30d`.
- Indexes:
  - `idx_encounters_patient` on `patient_nbr`
  - `idx_encounters_readmitted_30d` on `readmitted_30d`
  - `idx_encounters_age` on `age`
  - `idx_encounters_admission_type` on `admission_type_id`
  - `idx_encounters_diag1_group` on `diag_1_group`

### 3.2 SQL Security Guardrails
The interactive SQL Explorer isolates analytics from harmful data mutations:
- AST and regular expression tokenization intercept mutating statements: `DROP`, `DELETE`, `TRUNCATE`, `ALTER`, `UPDATE`, `INSERT`, `ATTACH`, `DETACH`.
- Only queries commencing with `SELECT`, `WITH`, or `EXPLAIN` are permitted for execution.
