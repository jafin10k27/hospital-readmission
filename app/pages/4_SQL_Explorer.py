"""SQL Analytical Explorer Dashboard Page (FR-4, FR-8)."""

import time

import plotly.express as px
import streamlit as st

from app.app_utils import apply_custom_css, get_pipeline_state, render_clinical_disclaimer
from hospital_readmission.sql_queries import PREDEFINED_QUERIES, SQLAnalyticsService

st.set_page_config(
    page_title="SQL Analytics Explorer | Hospital Readmission",
    page_icon="💾",
    layout="wide",
)

apply_custom_css()

st.markdown('<div class="main-header">SQL Analytical Explorer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Query the SQLite relational store with curated queries or a secure read-only SQL editor.</div>',
    unsafe_allow_html=True,
)

render_clinical_disclaimer()

state = get_pipeline_state()
sql_service = SQLAnalyticsService(state.database_manager)

tab1, tab2 = st.tabs(["📚 Predefined Analytical Queries", "⚡ Custom Read-Only SQL Editor"])

with tab1:
    st.subheader("Curated Healthcare Analytical Queries")

    query_names = list(PREDEFINED_QUERIES.keys())
    selected_query_name = st.selectbox("Select Analytical SQL Query", query_names, index=0)

    sql_code = PREDEFINED_QUERIES[selected_query_name].strip()
    with st.expander("View SQL Source Code", expanded=True):
        st.code(sql_code, language="sql")

    if st.button("▶ Run Curated Query", key="btn_run_curated", type="primary"):
        start_t = time.perf_counter()
        try:
            df_result = sql_service.run_predefined_query(selected_query_name)
            elapsed = time.perf_counter() - start_t
            st.success(f"Executed in {elapsed*1000:.1f} ms — Returned {len(df_result):,} row(s)")

            st.dataframe(df_result, use_container_width=True, hide_index=True)

            # Auto-visualize if suitable
            if "readmission_rate_pct" in df_result.columns and len(df_result.columns) >= 2:
                cat_col = df_result.columns[0]
                fig = px.bar(
                    df_result,
                    x=cat_col,
                    y="readmission_rate_pct",
                    text="readmission_rate_pct",
                    title=f"<b>{selected_query_name}</b>",
                    color="readmission_rate_pct",
                    color_continuous_scale="Reds",
                )
                fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
                fig.update_layout(template="plotly_white", xaxis_tickangle=-30)
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"SQL Execution Error: {e}")

with tab2:
    st.subheader("Secure Read-Only SQL Query Console")
    st.markdown(
        "Execute ad-hoc SELECT or WITH queries against the `encounters` table. "
        "Destructive commands (`DROP`, `DELETE`, `ALTER`, `UPDATE`, `INSERT`) are prohibited."
    )

    sample_custom = """-- Sample readmission query by medication count
SELECT
    num_medications,
    COUNT(*) AS encounter_count,
    ROUND(AVG(readmitted_30d) * 100.0, 2) AS readmission_rate_pct
FROM encounters
GROUP BY num_medications
HAVING COUNT(*) > 50
ORDER BY num_medications ASC;"""

    custom_sql = st.text_area("SQL Statement", value=sample_custom, height=180)

    if st.button("▶ Execute SQL", key="btn_run_custom"):
        start_t = time.perf_counter()
        try:
            df_custom = sql_service.run_custom_query(custom_sql)
            elapsed = time.perf_counter() - start_t
            st.success(f"Query returned {len(df_custom):,} rows in {elapsed*1000:.1f} ms")
            st.dataframe(df_custom, use_container_width=True, hide_index=True)
        except PermissionError as pe:
            st.error(f"Security Guardrail Triggered: {pe}")
        except Exception as e:
            st.error(f"Query Execution Failed: {e}")
