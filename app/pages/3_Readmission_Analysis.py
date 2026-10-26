"""Readmission Association Analysis Dashboard Page (FR-7, FR-8)."""

import streamlit as st

from app.app_utils import apply_custom_css, get_pipeline_state, render_clinical_disclaimer
from hospital_readmission.readmission_analysis import ReadmissionAnalyzer
from hospital_readmission.visualizations import plot_readmission_rate_by_group

st.set_page_config(
    page_title="Readmission Analysis | Hospital Readmission",
    page_icon="🔬",
    layout="wide",
)

apply_custom_css()

st.markdown('<div class="main-header">30-Day Readmission Association Analysis</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Bivariate risk profiling, 95% Wilson confidence intervals, effect sizes, and hypothesis testing.</div>',
    unsafe_allow_html=True,
)

render_clinical_disclaimer()

state = get_pipeline_state()
analyzer = ReadmissionAnalyzer(target_col="readmitted_30d")

tab1, tab2, tab3 = st.tabs([
    "📈 Bivariate Risk Profiles",
    "🧪 Categorical Hypothesis Tests (Chi-Square)",
    "📐 Continuous Comparisons (Mann-Whitney U)",
])

with tab1:
    st.subheader("Subgroup Readmission Rate with 95% Wilson Confidence Intervals")

    dimension_options = [
        ("Age Cohort", "age"),
        ("Gender", "gender"),
        ("Race", "race"),
        ("Admission Type", "admission_type_id_desc"),
        ("Discharge Disposition", "discharge_disposition_id_desc"),
        ("Primary Diagnosis Group", "diag_1_group"),
        ("Prior Inpatient Visits", "number_inpatient"),
        ("Emergency Visits", "number_emergency"),
        ("Medication Change", "change"),
        ("Diabetes Medication Prescribed", "diabetesMed"),
        ("HbA1c Result", "A1Cresult"),
        ("Insulin Regimen", "insulin"),
    ]

    valid_options = [(label, col) for label, col in dimension_options if col in state.cleaned_df.columns]
    label_to_col = dict(valid_options)

    selected_label = st.selectbox(
        "Select Clinical or Demographic Dimension",
        list(label_to_col.keys()),
        index=0,
    )
    selected_col = label_to_col[selected_label]

    rate_df = analyzer.calculate_group_rates(state.cleaned_df, group_col=selected_col)

    if not rate_df.empty:
        # Display Plotly chart
        fig_rates = plot_readmission_rate_by_group(
            rate_df,
            group_col_name=selected_label,
            title=f"<b>30-Day Readmission Rate by {selected_label}</b>",
        )
        st.plotly_chart(fig_rates, use_container_width=True)

        st.write("### Subgroup Statistics & Denominators")
        st.dataframe(
            rate_df[[
                "category",
                "total_encounters",
                "readmitted_count",
                "readmission_rate_pct",
                "ci_lower_pct",
                "ci_upper_pct",
                "percentage_of_cohort",
            ]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning(f"No valid data to calculate readmission rates for {selected_label}.")

with tab2:
    st.subheader("Chi-Square Independence Tests with FDR Correction")
    st.markdown(
        "Evaluates whether categorical variables have a statistically significant relationship "
        "with 30-day readmission. Corrected for multiple comparisons using the Benjamini-Hochberg False Discovery Rate (FDR)."
    )

    cat_cols_to_test = [
        "age",
        "gender",
        "race",
        "admission_type_id_desc",
        "discharge_disposition_id_desc",
        "diag_1_group",
        "change",
        "diabetesMed",
        "A1Cresult",
        "insulin",
        "metformin",
    ]

    cat_test_df = analyzer.run_all_categorical_tests(state.cleaned_df, cat_cols_to_test)

    if not cat_test_df.empty:
        st.dataframe(
            cat_test_df[[
                "variable",
                "chi2_stat",
                "degrees_of_freedom",
                "p_value",
                "fdr_adjusted_p",
                "cramers_v",
                "effect_size_label",
                "is_valid_chi2",
            ]],
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Note: Effect sizes (Cramer's V) distinguish statistical significance from practical clinical magnitude.")
    else:
        st.info("No categorical features available for hypothesis testing.")

with tab3:
    st.subheader("Continuous Variable Rank-Sum Tests (Mann-Whitney U)")
    st.markdown(
        "Non-parametric two-group comparisons evaluating distribution shifts between "
        "readmitted (<30d) vs. non-readmitted hospital encounters."
    )

    num_cols_to_test = [
        "time_in_hospital",
        "num_lab_procedures",
        "num_procedures",
        "num_medications",
        "number_outpatient",
        "number_emergency",
        "number_inpatient",
        "number_diagnoses",
    ]

    num_test_df = analyzer.run_all_numerical_tests(state.cleaned_df, num_cols_to_test)

    if not num_test_df.empty:
        st.dataframe(
            num_test_df[[
                "variable",
                "readmitted_mean",
                "readmitted_median",
                "non_readmitted_mean",
                "non_readmitted_median",
                "p_value",
                "fdr_adjusted_p",
                "effect_size",
                "effect_size_metric",
            ]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No continuous features available for rank testing.")
