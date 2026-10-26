"""Data Visualization Module (FR-9).

Creates publication-ready, interactive Plotly visualizations for
healthcare encounter distributions, data quality, and readmission risk comparisons.
"""

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Healthcare-themed accessible color palette
PRIMARY_TEAL = "#0284c7"      # Sky Blue / Cyan
ACCENT_CORAL = "#f43f5e"      # Rose / Coral for 30d readmission
NEUTRAL_GRAY = "#64748b"      # Slate Gray
BACKGROUND_LIGHT = "#f8fafc"  # Off-white
SUCCESS_GREEN = "#10b981"


def plot_readmission_distribution(outcome_summary: Any) -> go.Figure:
    """Plots donut chart showing proportions of raw outcome categories."""
    raw_dist = outcome_summary.raw_distribution
    labels = list(raw_dist.keys())
    values = list(raw_dist.values())

    colors = []
    for label in labels:
        if str(label).strip() == "<30":
            colors.append(ACCENT_CORAL)
        elif str(label).strip() == ">30":
            colors.append("#fbbf24")
        else:
            colors.append(PRIMARY_TEAL)

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Encounters: %{value:,}<br>Share: %{percent}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title="<b>Distribution of Readmission Outcome</b><br><sup>Encounters with &lt;30 days indicate 30-day readmissions</sup>",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        margin=dict(t=80, b=40, l=40, r=40),
    )
    return fig


def plot_missingness_chart(missing_df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Plots horizontal bar chart of column missingness percentages."""
    sub = missing_df[missing_df["total_missing"] > 0].head(top_n).iloc[::-1]

    if sub.empty:
        fig = go.Figure()
        fig.add_annotation(text="No missing values identified in dataset", showarrow=False)
        return fig

    fig = go.Figure(
        data=[
            go.Bar(
                x=sub["missing_percentage"],
                y=sub["column"],
                orientation="h",
                marker=dict(
                    color=sub["missing_percentage"],
                    colorscale="Viridis",
                    showscale=True,
                    colorbar=dict(title="% Missing"),
                ),
                text=sub.apply(lambda r: f"{r['missing_percentage']:.1f}% ({r['total_missing']:,})", axis=1),
                textposition="auto",
                hovertemplate="<b>%{y}</b><br>Missing: %{x:.2f}%<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title=f"<b>Top {min(len(sub), top_n)} Columns by Missingness (%)</b>",
        xaxis=dict(title="Missing Percentage (%)", range=[0, 105]),
        yaxis=dict(title=""),
        template="plotly_white",
        margin=dict(t=60, b=40, l=150, r=40),
    )
    return fig


def plot_readmission_rate_by_group(
    rate_df: pd.DataFrame,
    group_col_name: str,
    title: str | None = None,
    color: str = ACCENT_CORAL,
) -> go.Figure:
    """Plots readmission rates across categories with 95% Wilson confidence intervals."""
    if rate_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available for display", showarrow=False)
        return fig

    # Calculate asymmetric error bar heights
    error_plus = rate_df["ci_upper_pct"] - rate_df["readmission_rate_pct"]
    error_minus = rate_df["readmission_rate_pct"] - rate_df["ci_lower_pct"]

    hover_text = [
        f"<b>{row['category']}</b><br>"
        f"30d Readmission Rate: {row['readmission_rate_pct']:.2f}%<br>"
        f"95% CI: [{row['ci_lower_pct']:.2f}%, {row['ci_upper_pct']:.2f}%]<br>"
        f"Readmitted: {row['readmitted_count']:,} / {row['total_encounters']:,}<br>"
        f"Share of Cohort: {row['percentage_of_cohort']:.1f}%"
        for _, row in rate_df.iterrows()
    ]

    fig = go.Figure(
        data=[
            go.Bar(
                x=rate_df["category"],
                y=rate_df["readmission_rate_pct"],
                error_y=dict(
                    type="data",
                    symmetric=False,
                    array=error_plus,
                    arrayminus=error_minus,
                    color="#334155",
                    thickness=1.5,
                    width=4,
                ),
                marker=dict(color=color, line=dict(color="#1e293b", width=1)),
                hovertext=hover_text,
                hoverinfo="text",
            )
        ]
    )

    chart_title = title or f"<b>30-Day Readmission Rate by {group_col_name}</b><br><sup>Error bars depict 95% Wilson Score Confidence Intervals</sup>"
    fig.update_layout(
        title=chart_title,
        xaxis=dict(title=group_col_name, tickangle=-30),
        yaxis=dict(title="30-Day Readmission Rate (%)", rangemode="tozero"),
        template="plotly_white",
        margin=dict(t=70, b=80, l=50, r=40),
    )
    return fig


def plot_numerical_distribution_by_outcome(
    df: pd.DataFrame,
    num_col: str,
    outcome_col: str = "readmitted_30d",
) -> go.Figure:
    """Plots comparative distribution (box plot + violin or strip) for a continuous variable."""
    if num_col not in df.columns or outcome_col not in df.columns:
        fig = go.Figure()
        return fig

    sub = df[[num_col, outcome_col]].dropna().copy()
    sub[num_col] = pd.to_numeric(sub[num_col], errors="coerce")
    sub = sub.dropna()

    sub["Outcome"] = sub[outcome_col].map({1: "Readmitted <30d", 0: "Not Readmitted <30d"})

    fig = px.box(
        sub,
        x="Outcome",
        y=num_col,
        color="Outcome",
        color_discrete_map={"Readmitted <30d": ACCENT_CORAL, "Not Readmitted <30d": PRIMARY_TEAL},
        points="outliers",
        title=f"<b>Distribution of {num_col} by 30-Day Readmission Status</b>",
    )

    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        yaxis=dict(title=num_col),
        xaxis=dict(title=""),
        margin=dict(t=60, b=40, l=50, r=40),
    )
    return fig
