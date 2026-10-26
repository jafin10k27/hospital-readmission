"""Exploratory Data Analysis Dashboard Page (FR-6, FR-8)."""

import plotly.express as px
import streamlit as st

from app.app_utils import apply_custom_css, get_pipeline_state, render_clinical_disclaimer
from hospital_readmission.exploratory_analysis import ExploratoryDataAnalyzer
from hospital_readmission.visualizations import plot_numerical_distribution_by_outcome

st.set_page_config(
    page_title="Exploratory Analysis | Hospital Readmission",
    page_icon="📈",
    layout="wide",
)

apply_custom_css()

st.markdown('<div class="main-header">Exploratory Data Analysis</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Parametric and non-parametric distributions, clinical frequency tables, and correlation analysis.</div>',
    unsafe_allow_html=True,
)

render_clinical_disclaimer()

state = get_pipeline_state()
eda = ExploratoryDataAnalyzer()

num_summaries = eda.compute_numerical_summaries(state.cleaned_df)
corr_matrix = eda.compute_correlation_matrix(state.cleaned_df)

tab1, tab2, tab3 = st.tabs([
    "🔢 Numerical Summary & Distributions",
    "📊 Categorical Frequencies",
    "🔗 Correlation Analysis",
])

with tab1:
    st.subheader("Descriptive Statistics for Continuous Clinical Attributes")
    st.dataframe(num_summaries, use_container_width=True, hide_index=True)

    st.write("---")
    st.subheader("Continuous Variable Distribution by Readmission Status")

    num_vars = [c for c in num_summaries["variable"].tolist() if c in state.cleaned_df.columns]
    selected_num_var = st.selectbox(
        "Select Continuous Measurement to Inspect",
        num_vars,
        index=0 if num_vars else None,
    )

    if selected_num_var:
        fig_num = plot_numerical_distribution_by_outcome(
            state.cleaned_df,
            num_col=selected_num_var,
            outcome_col="readmitted_30d",
        )
        st.plotly_chart(fig_num, use_container_width=True)

with tab2:
    st.subheader("Categorical Feature Distributions")
    cat_candidates = [
        "age",
        "gender",
        "race",
        "admission_type_id_desc",
        "discharge_disposition_id_desc",
        "diag_1_group",
        "max_glu_serum",
        "A1Cresult",
        "insulin",
        "change",
        "diabetesMed",
    ]
    available_cats = [c for c in cat_candidates if c in state.cleaned_df.columns]

    selected_cat = st.selectbox("Select Categorical Feature", available_cats, index=0)

    if selected_cat:
        dist_df = eda.compute_categorical_distribution(state.cleaned_df, column=selected_cat)

        col_left, col_right = st.columns([1.2, 1.0])
        with col_left:
            fig_bar = px.bar(
                dist_df,
                x="category",
                y="encounter_count",
                text="percentage",
                title=f"<b>Encounter Distribution: {selected_cat}</b>",
                color="encounter_count",
                color_continuous_scale="Blues",
            )
            fig_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_bar.update_layout(template="plotly_white", xaxis_tickangle=-30)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_right:
            st.write("#### Frequency Table")
            st.dataframe(dist_df, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Spearman Rank Correlation Matrix")
    st.markdown(
        "Evaluates monotonic rank relationships between continuous utilization and clinical variables. "
        "Spearman rank correlation is robust to heavy right-skewed utilization metrics."
    )

    if not corr_matrix.empty:
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="<b>Spearman Rank Correlation Heatmap</b>",
        )
        fig_corr.update_layout(template="plotly_white")
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("Insufficient continuous features for correlation analysis.")
