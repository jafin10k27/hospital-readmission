"""Streamlit UI Utility and Styling Module."""

import streamlit as st

from hospital_readmission.pipeline import HealthcarePipeline, PipelineState


def apply_custom_css():
    """Injects modern, clinical-grade styling for Streamlit."""
    st.markdown(
        """
        <style>
        /* Modern Healthcare Typography and Palette */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .main-header {
            font-size: 2.1rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.2rem;
        }

        .sub-header {
            font-size: 1.05rem;
            color: #475569;
            margin-bottom: 1.5rem;
        }

        .metric-card {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 18px 20px;
            text-align: center;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        }

        .metric-value {
            font-size: 1.9rem;
            font-weight: 700;
            color: #0284c7;
            margin-bottom: 4px;
        }

        .metric-label {
            font-size: 0.82rem;
            color: #64748b;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.05em;
        }

        .clinical-disclaimer {
            background-color: #fff1f2;
            border-left: 4px solid #f43f5e;
            padding: 12px 18px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            color: #881337;
        }

        .info-callout {
            background-color: #f0f9ff;
            border-left: 4px solid #0284c7;
            padding: 12px 18px;
            border-radius: 4px;
            margin-bottom: 16px;
            font-size: 0.9rem;
            color: #0c4a6e;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_clinical_disclaimer():
    """Renders non-causal exploratory disclaimer."""
    st.markdown(
        """
        <div class="clinical-disclaimer">
            <strong>Clinical & Methodological Notice:</strong> This platform investigates statistical associations with 30-day hospital readmissions.
            Identified patterns are exploratory and do not establish clinical causality or constitute a prospectively validated predictive decision device.
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_pipeline_state(force_reload: bool = False) -> PipelineState:
    """Retrieves or executes the pipeline and caches the state in session_state."""
    if "pipeline_state" not in st.session_state or force_reload:
        with st.spinner("Executing healthcare analytics pipeline (ingestion, validation, cleaning, SQL)..."):
            pipeline = HealthcarePipeline()
            # If dataset exists, run with standard parameters
            nrows = st.session_state.get("nrows_limit", None)
            dedup = st.session_state.get("dedup_strategy", "keep_all")
            state = pipeline.run(nrows=nrows, patient_dedup_strategy=dedup)
            st.session_state["pipeline_state"] = state
    return st.session_state["pipeline_state"]


def format_count(value: int | float | None, fallback: str = "N/A") -> str:
    """Safely formats an integer count with comma separators or returns fallback."""
    if value is not None and str(value).lower() not in ("none", "nan", "<na>"):
        try:
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return fallback
    return fallback
