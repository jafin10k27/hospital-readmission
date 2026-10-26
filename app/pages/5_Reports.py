"""Reports and Exports Dashboard Page (FR-8, FR-10, FR-11)."""

import streamlit as st

from app.app_utils import apply_custom_css, get_pipeline_state, render_clinical_disclaimer
from hospital_readmission.readmission_analysis import ReadmissionAnalyzer
from hospital_readmission.reporting import ReportGenerator

st.set_page_config(
    page_title="Reports & Exports | Hospital Readmission",
    page_icon="📑",
    layout="wide",
)

apply_custom_css()

st.markdown('<div class="main-header">Reproducible Reports & Data Exports</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Generate and download comprehensive HTML/PDF analytical dossiers, cleaned datasets, and audit logs.</div>',
    unsafe_allow_html=True,
)

render_clinical_disclaimer()

state = get_pipeline_state()
analyzer = ReadmissionAnalyzer(target_col="readmitted_30d")
reporter = ReportGenerator(state.config.reports_dir)

# Prepare Summary Data for Reports
age_rates = analyzer.calculate_group_rates(state.cleaned_df, "age")
cat_tests = analyzer.run_all_categorical_tests(
    state.cleaned_df,
    ["age", "gender", "admission_type_id_desc", "diag_1_group", "change", "diabetesMed"],
)

report_payload = {
    "dataset_name": state.ingestion_metadata.source_path.split("/")[-1],
    "total_encounters": len(state.cleaned_df),
    "unique_patients": state.quality_summary.unique_patients,
    "readmission_rate": state.outcome_summary.readmission_rate_pct,
    "readmitted_count": state.outcome_summary.readmitted_30d_count,
    "exact_duplicates": state.validation_report.exact_duplicates,
    "columns_with_missing": len([i for i in state.validation_report.issues if i.issue_type == "high_missingness"]),
    "cleaning_ops_count": len(state.cleaning_log_df),
    "associations_table": age_rates.to_dict(orient="records"),
    "statistical_tests": cat_tests.to_dict(orient="records"),
}

# Generate both reports
html_path = reporter.generate_html_report(report_payload)
pdf_path = None
try:
    pdf_path = reporter.generate_pdf_report(report_payload)
except Exception as e:
    st.warning(f"PDF generation notice: {e}")

col_left, col_right = st.columns([1.1, 1.0])

with col_left:
    st.subheader("Download Analytical Reports")

    # HTML Download
    if html_path.exists():
        with open(html_path, encoding="utf-8") as f:
            html_bytes = f.read().encode("utf-8")

        st.download_button(
            label="📄 Download HTML Dossier (.html)",
            data=html_bytes,
            file_name="readmission_analytical_report.html",
            mime="text/html",
            use_container_width=True,
        )

    # PDF Download
    if pdf_path and pdf_path.exists():
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        st.download_button(
            label="📕 Download PDF Analytical Dossier (.pdf)",
            data=pdf_bytes,
            file_name="readmission_analytical_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.write("---")
    st.subheader("Data & Audit Log Exports")

    # Cleaned CSV
    cleaned_csv = state.cleaned_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="💾 Download Cleaned Encounter Data (.csv)",
        data=cleaned_csv,
        file_name="cleaned_hospital_encounters.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # Validation Log CSV
    val_csv = state.validation_report.to_dataframe().to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⚠️ Download Validation Log (.csv)",
        data=val_csv,
        file_name="validation_log.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # Cleaning Log CSV
    cleaning_csv = state.cleaning_log_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="🧹 Download Cleaning Transformation Log (.csv)",
        data=cleaning_csv,
        file_name="cleaning_audit_log.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col_right:
    st.subheader("Live Analytical Report Preview")
    if html_path.exists():
        with open(html_path, encoding="utf-8") as f:
            preview_html = f.read()
        st.components.v1.html(preview_html, height=650, scrolling=True)
