# Hospital Readmission Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![Dashboard](https://img.shields.io/badge/Dashboard-Streamlit-red.svg)](https://streamlit.io/)
[![Visualizations](https://img.shields.io/badge/Visualizations-Plotly-teal.svg)](https://plotly.com/)
[![Testing](https://img.shields.io/badge/Tests-pytest%2031%2F31%20passing-brightgreen.svg)](https://docs.pytest.org/)
[![Linting](https://img.shields.io/badge/Linter-Ruff%20Clean-purple.svg)](https://github.com/astral-sh/ruff)

An end-to-end healthcare data engineering and statistical intelligence platform that ingests real hospital encounter records, executes automated data quality audits, applies an audited cleaning pipeline, persists data in a relational SQLite store, analyzes 30-day hospital readmissions with Wilson confidence intervals and hypothesis testing, and provides an interactive Streamlit dashboard with downloadable analytical dossiers.

---

## 1. System Architecture

```mermaid
graph TD
    A[Raw Healthcare CSV<br/>UCI Diabetes 101k Encounters] --> B[Data Ingestion Engine<br/>FR-1: Encoding & Metadata]
    B --> C[Data Quality & Validation Engine<br/>FR-2: Sentinels, Duplicates, Types]
    C --> D[Audited Cleaning Pipeline<br/>FR-3: Normalization & ICD-9 Grouping]
    D --> E[Outcome Definition Engine<br/>FR-5: Binarized 30-Day Endpoint]
    E --> F[(SQLite Relational Store)<br/>FR-4: Encounters & Indexes]
    F --> G[SQL Analytical Engine<br/>FR-4: Curated Parameterized Queries]
    F --> H[Statistical Inference Engine<br/>FR-7: Wilson CIs, Chi-Square, Mann-Whitney]
    G --> I[Interactive Streamlit Dashboard<br/>FR-8 & FR-9: Plotly UI]
    H --> I
    I --> J[Report & Export Engine<br/>FR-10: Jinja2 HTML & ReportLab PDF]
```

---

## 2. Key Features

- **Real Healthcare Dataset Ingestion:** Built for the UCI Diabetes 130-US Hospitals (1999–2008) dataset with 101,766 hospital encounters and 50 clinical attributes.
- **Automated Data Quality Profiler:** Identifies exact duplicate rows, differentiates repeat patient admissions from duplicate records, detects sentinel missingness markers (`?`), and flags invariant attributes.
- **Audited Cleaning Pipeline:** Standardizes schemas, converts sentinels to `NaN`, strips sparse columns (>50% missingness such as body weight), joins human-readable ID descriptors, and maps ICD-9 primary diagnoses to clinical disease categories (Circulatory, Respiratory, Diabetes, Genitourinary, Neoplasms, etc.). Every operation is logged with rows before/after, justification, and reversibility flags.
- **Relational SQLite Store & SQL Security Guardrails:** Tables for `encounters`, `cleaning_log`, `validation_log`, and `data_quality_summary`. B-tree indexes on `patient_nbr`, `readmitted_30d`, and `age`. Includes an interactive SQL console with AST security guardrails blocking mutating statements (`DROP`, `DELETE`, `ALTER`, `UPDATE`).
- **Rigorous Statistical Modeling:**
  - 95% Wilson Score Confidence Intervals with continuity correction for binomial proportions.
  - Pearson's $\chi^2$ test of independence with Cramer's V effect size labels and minimum expected cell count verification.
  - Non-parametric Mann-Whitney U rank-sum test with rank-biserial correlations for skewed utilization metrics.
  - Benjamini-Hochberg False Discovery Rate (FDR) and Bonferroni adjustments.
- **Interactive Multi-Page Streamlit Dashboard:**
  - `Overview`: Key performance indicators, outcome donut chart, dataset status, sample preview.
  - `1_Data_Quality`: Missingness charts, validation audit table, and cleaning transformation history.
  - `2_Exploratory_Analysis`: Parametric/non-parametric continuous metrics, categorical frequencies, and Spearman rank correlation heatmap.
  - `3_Readmission_Analysis`: Bivariate readmission risk profiles with Wilson error bars and statistical hypothesis test summaries.
  - `4_SQL_Explorer`: Predefined curated SQL queries and custom read-only SQL editor.
  - `5_Reports`: Live report preview and download buttons for Jinja2 HTML dossiers, ReportLab PDF summaries, cleaned CSVs, and audit logs.

---

## 3. Project Directory Structure

```
Hospital Readmission/
├── PRD.md                             # Product Requirements Document
├── README.md                            # Comprehensive Platform Guide
├── pyproject.toml                       # Python package configuration & dependencies
├── .env.example                         # Environment configuration template
├── .gitignore                           # Git exclusion rules
├── config/
│   ├── settings.yaml                    # Centralized pipeline, cleaning, and stats settings
│   └── schema.yaml                      # Expected schema, valid ranges, and ICD-9 clusters
├── data/
│   ├── raw/                             # Raw CSV data and lookup files
│   │   ├── diabetic_data.csv            # UCI real encounter dataset (101,766 records)
│   │   └── IDS_mapping.csv              # Admission/discharge lookup mappings
│   ├── processed/                       # Cleaned dataset and SQLite database
│   │   └── hospital_readmission.db      # SQLite relational database
│   └── external/                        # External data assets
├── reports/
│   └── generated/                       # Output HTML and PDF analytical reports
├── notebooks/
│   └── exploratory_analysis.ipynb       # Documented research notebook
├── src/
│   └── hospital_readmission/            # Core Python package
│       ├── __init__.py                  # Version and package metadata
│       ├── config.py                    # Settings and schema loader
│       ├── ingestion.py                 # CSV loader and encoding fallbacks (FR-1)
│       ├── schema_validation.py         # Automated validation engine (FR-2)
│       ├── cleaning.py                  # Audited cleaning pipeline (FR-3)
│       ├── outcomes.py                  # 30-day readmission endpoint binarization (FR-5)
│       ├── database.py                  # SQLite storage, indexing, and connection manager (FR-4)
│       ├── sql_queries.py               # Predefined SQL analytics & security guardrails (FR-4)
│       ├── quality_analysis.py          # Missingness, duplicate, and cardinality metrics (FR-6)
│       ├── exploratory_analysis.py      # Numerical statistics & correlations (FR-6)
│       ├── readmission_analysis.py      # Bivariate risk analysis & group rates (FR-7)
│       ├── statistics.py                # Wilson CIs, Chi-square, Mann-Whitney, FDR (FR-7)
│       ├── visualizations.py            # Plotly interactive healthcare charts (FR-9)
│       ├── reporting.py                 # HTML & PDF analytical report generation (FR-10)
│       ├── export.py                    # Data and metadata export utilities (FR-11)
│       ├── pipeline.py                  # End-to-end pipeline orchestrator
│       └── logging_config.py            # Centralized logging configuration
├── app/
│   ├── streamlit_app.py                 # Main dashboard application (Overview)
│   ├── app_utils.py                     # Custom clinical CSS, disclaimers, and state caching
│   └── pages/
│       ├── 1_Data_Quality.py            # Data quality, sentinels, and cleaning logs
│       ├── 2_Exploratory_Analysis.py    # Continuous/categorical distributions & correlations
│       ├── 3_Readmission_Analysis.py    # Subgroup readmission rates & hypothesis tests
│       ├── 4_SQL_Explorer.py            # Curated and custom read-only SQL queries
│       └── 5_Reports.py                 # Downloadable reports (HTML, PDF) & CSV exports
├── sql/
│   ├── schema.sql                       # Database DDL, table constraints, and indexes
│   └── analytical_queries.sql           # Curated analytical SQL queries
└── tests/
    ├── fixtures/
    │   └── synthetic_encounters.py      # Deterministic synthetic test fixture
    ├── unit/
    │   ├── test_ingestion.py            # Tests for FR-1 CSV loading and errors
    │   ├── test_validation.py           # Tests for FR-2 schema validation
    │   ├── test_cleaning.py             # Tests for FR-3 cleaning and ICD-9 mapping
    │   ├── test_outcomes.py             # Tests for FR-5 readmission binarization
    │   ├── test_database.py             # Tests for FR-4 SQLite persistence and guardrails
    │   ├── test_statistics.py           # Tests for FR-7 Wilson CIs and tests
    │   └── test_reporting_and_export.py # Tests for FR-10 and FR-11 reports and exports
    └── integration/
        └── test_end_to_end_pipeline.py  # Complete end-to-end pipeline test
```

---

## 4. Setup & Installation

### Prerequisites
- Python 3.11+ (CPython 3.11 recommended)
- `uv` (recommended) or standard `pip` / `venv`
- Linux (compatible with Arch Linux, Ubuntu, Debian, RHEL) or macOS

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd "Hospital Readmission"
   ```

2. **Set up virtual environment:**
   Using `uv`:
   ```bash
   uv venv --python 3.11 .venv
   source .venv/bin/activate
   uv pip install -e .
   ```
   Or standard `python`:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

3. **Verify Dataset Acquisition:**
   The real dataset (`data/raw/diabetic_data.csv` and `data/raw/IDS_mapping.csv`) is downloaded automatically if needed. To trigger automated download directly:
   ```bash
   python -c "
   import os, urllib.request, zipfile
   os.makedirs('data/raw', exist_ok=True)
   zip_path = 'data/raw/diabetes.zip'
   url = 'https://archive.ics.uci.edu/static/public/296/diabetes+130-us+hospitals+for+years+1999-2008.zip'
   urllib.request.urlretrieve(url, zip_path)
   with zipfile.ZipFile(zip_path, 'r') as z: z.extractall('data/raw/')
   "
   ```
   *Manual Fallback:* Download the archive from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008) and extract `diabetic_data.csv` and `IDS_mapping.csv` into `data/raw/`.

---

## 5. Running the Application

Launch the Streamlit dashboard using:
```bash
streamlit run app/streamlit_app.py
```
Open your browser at `http://localhost:8501`.

---

## 6. Running Automated Tests & Linting

Run the test suite across all 31 unit and integration tests:
```bash
pytest tests/
```

Execute code quality and linting verification:
```bash
ruff check .
```

---

## 7. Clinical & Methodological Limitations

> [!WARNING]
> **Exploratory Observational Analysis:** All findings represent observational statistical associations and must not be interpreted as causal relationships or a validated clinical prediction model.

1. **Unmeasured Confounding:** Key determinants of readmission (e.g., social determinants of health, housing stability, outpatient medication compliance, post-discharge primary care follow-up) are not captured in hospital billing encounters.
2. **Right Censoring:** Readmissions occurring at non-participating healthcare facilities outside the 130-hospital network are recorded as non-readmissions (`NO`), leading to potential undercounting.
3. **Historic Context:** The dataset reflects encounters from 1999–2008; clinical standards and inpatient care transition pathways have evolved significantly.
