"""Streamlit Application Main Entrypoint - Overview Page (FR-8)."""

import streamlit as st

from app.app_utils import apply_custom_css, get_pipeline_state, render_clinical_disclaimer
from hospital_readmission.config import AppConfig
from hospital_readmission.visualizations import plot_readmission_distribution

st.set_page_config(
    page_title="Hospital Readmission Intelligence Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_css()

# Sidebar: Configuration & Controls
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/hospital.png", width=64)
    st.title("Hospital Analytics")
    st.caption("Intelligence & Readmission Research Platform")
    st.divider()

    st.subheader("Dataset Configuration")
    config = AppConfig.load()

    dataset_choice = st.selectbox(
        "Source Dataset",
        ["UCI Diabetes 130-US Hospitals (Default)", "Custom Local CSV Path"],
        help="Select real healthcare encounter dataset source.",
    )

    custom_path = None
    if dataset_choice == "Custom Local CSV Path":
        custom_path = st.text_input("CSV File Path", value=str(config.raw_data_path))

    row_limit_option = st.selectbox(
        "Data Load Scope",
        ["Full Dataset (~101k Encounters)", "Preview 10,000 Records", "Preview 25,000 Records"],
        index=0,
    )

    nrows_map = {
        "Full Dataset (~101k Encounters)": None,
        "Preview 10,000 Records": 10000,
        "Preview 25,000 Records": 25000,
    }
    selected_nrows = nrows_map[row_limit_option]

    dedup_strategy = st.radio(
        "Patient Encounter Scope",
        ["All Longitudinal Encounters", "Initial Encounter Per Patient"],
        index=0,
        help="Distinguishes exact duplicate rows from repeated patient visits.",
    )
    dedup_val = "keep_first" if "Initial" in dedup_strategy else "keep_all"

    # Store in session state
    st.session_state["nrows_limit"] = selected_nrows
    st.session_state["dedup_strategy"] = dedup_val

    if st.button("🔄 Reload & Re-run Pipeline", use_container_width=True):
        st.session_state.pop("pipeline_state", None)
        st.rerun()

    st.divider()
    st.info("System Engine: Python 3.11 • SQLite • Pandas • Plotly • SciPy")

# Header
st.markdown('<div class="main-header">Hospital Readmission Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Rigorous healthcare data quality assessment, 30-day readmission association modeling, and SQL exploration.</div>',
    unsafe_allow_html=True,
)

render_clinical_disclaimer()

# Load Pipeline State
try:
    state = get_pipeline_state()
except Exception as e:
    st.error(f"Error loading healthcare pipeline: {e}")
    st.stop()

# Headline Metrics Cards
total_encounters = len(state.cleaned_df)
unique_patients = state.quality_summary.unique_patients
outcome = state.outcome_summary

unique_patients_display = (
    f"{unique_patients:,}"
    if unique_patients is not None
    else "N/A"
)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{total_encounters:,}</div>
            <div class="metric-label">Analyzed Encounters</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{unique_patients_display}</div>
            <div class="metric-label">Unique Patients</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #f43f5e;">{outcome.readmission_rate_pct:.2f}%</div>
            <div class="metric-label">30d Readmission Rate</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{outcome.readmitted_30d_count:,}</div>
            <div class="metric-label">30d Readmissions</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col5:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #64748b;">{state.quality_summary.overall_missing_pct:.1f}%</div>
            <div class="metric-label">Missing Cell Rate</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")
st.write("")

# Main View: 2 Columns (Outcome Distribution + Pipeline Status)
left_col, right_col = st.columns([1.1, 1.0])

with left_col:
    st.subheader("Outcome Target Distribution")
    fig_dist = plot_readmission_distribution(outcome)
    st.plotly_chart(fig_dist, use_container_width=True)

with right_col:
    st.subheader("Dataset Provenance & Quality Profile")
    st.markdown(
        f"""
        - **Data Source:** UCI Machine Learning Repository (Diabetes 130-US Hospitals 1999–2008)
        - **Raw Encounter Records:** `{state.ingestion_metadata.row_count:,}`
        - **Cleaned Dataset Records:** `{len(state.cleaned_df):,}`
        - **Total Clinical Attributes:** `{state.ingestion_metadata.column_count}`
        - **Exact Duplicate Rows:** `{state.validation_report.exact_duplicates}`
        - **Ingestion Timestamp:** `{state.ingestion_metadata.ingestion_timestamp}`
        - **SQLite Database Path:** `{state.config.database_path}`
        """
    )
    st.markdown(
        """
        <div class="info-callout">
            <strong>Endpoint Classification:</strong> In accordance with CMS Hospital Readmissions Reduction Program (HRRP) conventions,
            the binary endpoint isolates readmission occurring <em>&lt;30 days</em> post-discharge from elective or late readmissions (<em>&gt;30 days</em>).
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# Sample Encounters Preview
st.subheader("Cleaned Clinical Encounters Sample (Head 10)")
st.dataframe(
    state.cleaned_df.head(10),
    use_container_width=True,
    hide_index=True,
)
