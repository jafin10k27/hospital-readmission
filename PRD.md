# Product Requirements Document (PRD)
## Hospital Readmission Intelligence Platform

**Project type:** Healthcare data analytics and exploratory research  
**Primary stack:** Python, Pandas, SQL, SQLite, Streamlit, Plotly, pytest  
**Development environment:** Linux-compatible (including Arch Linux)  
**Target:** Complete, tested, documented, portfolio-ready application  

---

### 1. Product Overview
Build a complete healthcare analytics application that processes hospital encounter records, evaluates dataset quality, analyzes variables associated with 30-day hospital readmissions, and presents reproducible findings through an interactive dashboard and downloadable reports.

The application implements a complete workflow:  
`Data ingestion → Schema validation → Data quality assessment → Cleaning → SQL storage and querying → Exploratory data analysis → Readmission analysis → Visualization → Report generation → Export`.

The system operates on a real dataset and calculates all statistics from the loaded data. It never invents patient records, statistics, analysis results, or model performance.

### 2. Problem Statement
Hospital readmissions can increase healthcare costs and may indicate opportunities to improve care transitions and follow-up. Healthcare encounter datasets contain missing values, duplicate records, inconsistent data types, imbalanced outcome classes, and potentially misleading associations. This project investigates data quality and identifies variables associated with readmission within 30 days. The analysis is exploratory. Associations must not be presented as proof of causation, and findings must not be presented as a clinically validated prediction system.

### 3. Core Capabilities
- **Real Dataset Ingestion:** UCI Diabetes 130-US Hospitals (101,766 records, 50 attributes).
- **Automated Validation:** Missingness, duplicates, sentinel markers (`?`), domain checks.
- **Audited Cleaning Pipeline:** Standardized column headers, sentinel conversion, deduplication logging, ICD-9 disease grouping.
- **SQLite Analytics Store:** Relational encounters table, indexes, curated parameterized queries, SQL security guardrails.
- **Statistical Modeling:** 95% Wilson Score confidence intervals, Chi-square independence tests, Mann-Whitney U rank-sum tests, FDR (Benjamini-Hochberg) adjustments.
- **Streamlit Interactive UI:** 5 comprehensive pages (Overview, Data Quality, Exploratory Analysis, Readmission Analysis, SQL Explorer, Reports).
- **Reproducible Reporting:** Jinja2 HTML and ReportLab PDF dossiers.
