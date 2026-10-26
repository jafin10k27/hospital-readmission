"""Data Quality and Validation Dashboard Page (FR-2, FR-8)."""

import pandas as pd
import streamlit as st

from app.app_utils import apply_custom_css, get_pipeline_state, render_clinical_disclaimer
from hospital_readmission.quality_analysis import QualityAnalyzer
from hospital_readmission.visualizations import plot_missingness_chart

st.set_page_config(
    page_title="Data Quality & Integrity | Hospital Readmission",
    page_icon="🔍",
    layout="wide",
)

apply_custom_css()

st.markdown('<div class="main-header">Data Quality & Validation Audit</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Automated data profiling, sentinel value tracking, missingness audits, and cleaning history.</div>',
    unsafe_allow_html=True,
)

render_clinical_disclaimer()

state = get_pipeline_state()
quality_analyzer = QualityAnalyzer()
missing_table = quality_analyzer.compute_missingness_table(state.raw_df)
cardinality_table = quality_analyzer.compute_cardinality_table(state.cleaned_df)
val_df = state.validation_report.to_dataframe()

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Missingness Profile",
    "⚠️ Validation Audit Log",
    "🧹 Cleaning History",
    "🧬 Cardinality & Types",
])

with tab1:
    st.subheader("Missingness & Sentinel Value Analysis")
    st.markdown(
        "Clinical datasets often encode missing values using sentinels such as `?`, `None`, or unmapped codes. "
        "The chart below identifies attributes with significant missing data."
    )

    top_n = st.slider("Number of top incomplete columns to display", min_value=5, max_value=25, value=12)
    fig_miss = plot_missingness_chart(missing_table, top_n=top_n)
    st.plotly_chart(fig_miss, use_container_width=True)

    st.write("### Detailed Missingness Breakdown")
    st.dataframe(
        missing_table[missing_table["total_missing"] > 0],
        use_container_width=True,
        hide_index=True,
    )

with tab2:
    st.subheader("Automated Validation Rules Engine")
    st.markdown(
        f"Validation evaluated **{len(val_df)} potential integrity issues** across dimensions, data types, and identifiers."
    )

    # Severity filter
    severities = st.multiselect(
        "Filter by Severity",
        ["ERROR", "WARNING", "INFO"],
        default=["ERROR", "WARNING", "INFO"],
    )

    filtered_val = val_df[val_df["severity"].isin(severities)] if not val_df.empty else pd.DataFrame()

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Errors (Critical)", state.validation_report.error_count)
    with col_b:
        st.metric("Warnings (Data Quality)", state.validation_report.warning_count)
    with col_c:
        st.metric("Informational", state.validation_report.info_count)

    st.write("")
    if not filtered_val.empty:
        st.dataframe(
            filtered_val,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No validation findings match selected severity filter.")

with tab3:
    st.subheader("Pipeline Cleaning Audit Trail")
    st.markdown(
        "Every data transformation is logged with exact row counts before/after, "
        "justification, and reversibility."
    )

    if not state.cleaning_log_df.empty:
        st.dataframe(
            state.cleaning_log_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No cleaning transformations recorded.")

with tab4:
    st.subheader("Attribute Cardinality & Inferred Data Types")
    st.markdown("Auditing unique value frequencies helps identify constant columns or high-cardinality identifiers.")

    st.dataframe(
        cardinality_table,
        use_container_width=True,
        hide_index=True,
    )
