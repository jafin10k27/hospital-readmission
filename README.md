# Hospital Readmission Analysis

An end-to-end data pipeline, SQLite analytics database, and Streamlit dashboard built to investigate 30-day hospital readmissions using the UCI Diabetes 130-US Hospitals dataset (~101k clinical encounters across 10 years).

The project handles the complete analytics workflow: raw CSV ingestion, schema validation, data cleaning with transformation logs, SQLite storage, statistical association testing, interactive visualization, and HTML/PDF report generation.

---

## What It Does

1. **Ingestion & Validation**: Loads the raw dataset, checks for encoding issues, identifies exact duplicate rows, tracks longitudinal patient visits (`patient_nbr`), audits sentinel missing values (`?`), and flags invalid categories or out-of-range numericals.
2. **Data Cleaning**: Replaces sentinel markers with `NaN`, drops columns with extreme missingness (>50% missing, e.g. `weight`), maps numeric IDs (admission type, discharge disposition, admission source) to readable clinical descriptions, and groups ICD-9 primary diagnosis codes into high-level categories (Circulatory, Respiratory, Digestive, Diabetes, Injury, etc.). Every operation is logged with rows before/after and reversibility notes.
3. **Outcome Binarization**: Maps the original `readmitted` field to a binary 30-day target (`<30` as positive; `>30` and `NO` as negative), while preserving the raw label.
4. **SQLite Analytics Engine**: Loads cleaned records into SQLite with B-tree indexes on frequent query columns (`patient_nbr`, `readmitted_30d`, `age`, `admission_type_id`). Includes a set of curated analytical queries and a read-only SQL console protected by security guardrails that block destructive statements (`DROP`, `DELETE`, `UPDATE`, `ALTER`).
5. **Statistical Analysis**:
   - 95% Wilson score confidence intervals for subgroup readmission rates.
   - Pearson's Chi-square tests of independence with Cramer's V effect sizes for categorical variables.
   - Mann-Whitney U rank-sum tests with rank-biserial correlations for skewed continuous variables (prior inpatient visits, length of stay, medication counts).
   - Benjamini-Hochberg False Discovery Rate (FDR) and Bonferroni corrections for multiple testing.
6. **Streamlit Dashboard**: A 5-page app covering dataset overview, data quality profile, exploratory analysis, readmission risk factors, SQL query explorer, and downloadable reports.
7. **Exportable Reports**: Generates downloadable HTML reports (via Jinja2) and PDF dossiers (via ReportLab) built directly from calculated metrics.

---

## Dataset

- **Source**: [UCI Machine Learning Repository — Diabetes 130-US Hospitals (1999–2008)](https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008)
- **Size**: 101,766 hospital encounters across 71,518 unique patients, with 50 clinical and demographic attributes.
- **Outcome definition**: The dataset's raw `readmitted` column distinguishes `<30` (readmitted within 30 days), `>30` (readmitted after 30 days), and `NO` (no readmission recorded). Following CMS HRRP guidelines, this project treats `<30` as the positive class (~8.8% in unique patient cohorts).

---

## Project Structure

```text
├── config/
│   ├── settings.yaml            # Pipeline, database, and statistical thresholds
│   └── schema.yaml              # Expected data types, valid ranges, and ICD-9 maps
├── data/
│   ├── raw/                     # Original CSVs (diabetic_data.csv, IDS_mapping.csv)
│   └── processed/               # SQLite database (hospital_readmission.db)
├── src/hospital_readmission/
│   ├── ingestion.py             # CSV reader with fallback encodings
│   ├── schema_validation.py     # Data quality checks & issue reporting
│   ├── cleaning.py              # Transformation pipeline & audit log
│   ├── outcomes.py              # 30-day readmission definition
│   ├── database.py              # SQLite storage, indexing, and connection handling
│   ├── sql_queries.py           # Predefined queries & SQL guardrails
│   ├── quality_analysis.py      # Missingness & cardinality summaries
│   ├── exploratory_analysis.py  # Descriptive statistics & correlations
│   ├── readmission_analysis.py  # Group rates, Wilson CIs, and test runners
│   ├── statistics.py            # Wilson score, Chi-square, Mann-Whitney U, FDR
│   ├── visualizations.py        # Plotly charts (Wilson error bars, distributions)
│   ├── reporting.py             # HTML (Jinja2) and PDF (ReportLab) generators
│   ├── export.py                # CSV/JSON exporters
│   └── pipeline.py              # End-to-end pipeline coordinator
├── app/
│   ├── streamlit_app.py         # Main dashboard (Overview)
│   ├── app_utils.py             # UI helpers, formatting, CSS
│   └── pages/
│       ├── 1_Data_Quality.py
│       ├── 2_Exploratory_Analysis.py
│       ├── 3_Readmission_Analysis.py
│       ├── 4_SQL_Explorer.py
│       └── 5_Reports.py
├── sql/
│   ├── schema.sql               # SQLite schema and indexes
│   └── analytical_queries.sql   # Standardized analytical queries
├── tests/                       # 34 pytest unit & integration tests
├── docs/
│   ├── data_dictionary.md       # Full 50-variable clinical dictionary
│   ├── methodology.md           # Statistical formulas & pipeline design
│   └── limitations.md           # Confounding, censoring, and clinical caveats
└── notebooks/
    └── exploratory_analysis.ipynb
```

---

## Setup & Quickstart

### 1. Clone the repository
```bash
git clone https://github.com/jafin10k27/hospital-readmission.git
cd hospital-readmission
```

### 2. Create virtual environment and install dependencies
Using `uv`:
```bash
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -e .
```

Or using standard `pip`:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Download the dataset (if not present)
The pipeline expects `diabetic_data.csv` and `IDS_mapping.csv` in `data/raw/`. To download directly from UCI:
```bash
python -c "
import urllib.request, zipfile, os
os.makedirs('data/raw', exist_ok=True)
url = 'https://archive.ics.uci.edu/static/public/296/diabetes+130-us+hospitals+for+years+1999-2008.zip'
urllib.request.urlretrieve(url, 'data/raw/data.zip')
with zipfile.ZipFile('data/raw/data.zip', 'r') as z: z.extractall('data/raw/')
"
```

### 4. Run the Streamlit Dashboard
```bash
streamlit run app/streamlit_app.py
```
Open `http://localhost:8501` in your browser.

---

## Running Tests & Linter

```bash
# Run the complete test suite (34 tests)
pytest tests/

# Run the linter
ruff check .
```

All tests run on synthetic fixture data with known expected values to verify ingestion, validation rules, cleaning logs, SQL aggregations, Wilson intervals, hypothesis tests, and report builders.

---

## Key Methodology Notes

- **Wilson Score Intervals**: For readmission rates, normal approximation (Wald intervals) breaks down near 0% and in small subgroups. We use Wilson score intervals with continuity correction, guaranteeing valid bounds `[0, 1]` and accurate coverage.
- **Non-Parametric Testing**: Hospital utilization counts (`number_inpatient`, `number_emergency`, `time_in_hospital`) are heavily right-skewed with high zero-inflation. We use Mann-Whitney U rank-sum tests and report rank-biserial correlations rather than standard Student's t-tests.
- **Multiple Comparisons**: When running tests across multiple clinical attributes simultaneously, raw p-values are adjusted using the Benjamini-Hochberg False Discovery Rate (FDR) procedure.

---

## Limitations

- **Retrospective Observational Data**: Observed associations (e.g. higher readmission rates in patients on insulin or with multiple prior admissions) reflect underlying disease severity and complexity, not treatment harm. They do not demonstrate causality.
- **Unmeasured Confounders**: Critical post-discharge factors—social determinants of health (SDOH), housing, outpatient medication adherence, and primary care follow-up—are not recorded in encounter data.
- **Right Censoring**: Readmissions outside the participating 130-hospital network are recorded as `NO`, which may underestimate true 30-day readmission rates.

See [`docs/limitations.md`](docs/limitations.md) and [`docs/methodology.md`](docs/methodology.md) for detailed clinical context and formulas.

---

## License

MIT
