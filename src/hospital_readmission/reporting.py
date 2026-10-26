"""Report Generation Module (FR-10).

Generates comprehensive, reproducible HTML (via Jinja2) and PDF (via ReportLab)
analytical reports from actual calculated statistics, quality findings, and research limitations.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Template

from hospital_readmission import __version__
from hospital_readmission.logging_config import setup_logger

logger = setup_logger(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hospital Readmission Intelligence Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #1e293b;
            background-color: #f8fafc;
            margin: 0;
            padding: 30px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: #ffffff;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        h1 { color: #0f172a; border-bottom: 2px solid #0284c7; padding-bottom: 12px; margin-top: 0; }
        h2 { color: #0369a1; margin-top: 32px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }
        h3 { color: #334155; margin-top: 24px; }
        .meta-box {
            background-color: #f1f5f9;
            border-left: 4px solid #0284c7;
            padding: 14px 20px;
            margin-bottom: 24px;
            font-size: 0.95em;
        }
        .alert-box {
            background-color: #fff1f2;
            border-left: 4px solid #f43f5e;
            padding: 14px 20px;
            margin-top: 20px;
            margin-bottom: 20px;
            font-size: 0.95em;
        }
        .kpi-container {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            margin: 20px 0;
        }
        .kpi-card {
            flex: 1;
            min-width: 180px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 16px;
            border-radius: 6px;
            text-align: center;
        }
        .kpi-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #0284c7;
        }
        .kpi-label {
            font-size: 0.85em;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0 24px 0;
            font-size: 0.92em;
        }
        th, td {
            text-align: left;
            padding: 10px 12px;
            border-bottom: 1px solid #e2e8f0;
        }
        th {
            background-color: #f8fafc;
            color: #475569;
            font-weight: 600;
        }
        tr:hover { background-color: #f1f5f9; }
        .badge {
            display: inline-block;
            padding: 3px 8px;
            font-size: 0.75em;
            font-weight: 600;
            border-radius: 4px;
        }
        .badge-error { background-color: #fee2e2; color: #991b1b; }
        .badge-warning { background-color: #fef3c7; color: #92400e; }
        .badge-info { background-color: #e0f2fe; color: #075985; }
        footer {
            margin-top: 40px;
            padding-top: 16px;
            border-top: 1px solid #e2e8f0;
            font-size: 0.85em;
            color: #94a3b8;
            text-align: center;
        }
    </style>
</head>
<body>
<div class="container">
    <h1>Hospital Readmission Intelligence Platform</h1>
    <div class="meta-box">
        <strong>Report Generation:</strong> {{ generated_at }}<br>
        <strong>Platform Engine:</strong> v{{ version }} | <strong>Environment:</strong> Python 3.11 / SQLite3<br>
        <strong>Dataset Provenance:</strong> {{ dataset_name }} ({{ total_encounters }} encounters processed)
    </div>

    <div class="alert-box">
        <strong>Exploratory Clinical Disclaimer:</strong> This report identifies exploratory associations with 30-day readmission in hospital encounter data. Observed associations do not establish medical causation, nor do they constitute a validated clinical risk score or diagnostic prediction device.
    </div>

    <h2>1. Executive Summary & KPIs</h2>
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-value">{{ "{:,}".format(total_encounters) }}</div>
            <div class="kpi-label">Analyzed Encounters</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">{{ "{:,}".format(unique_patients) if unique_patients else "N/A" }}</div>
            <div class="kpi-label">Unique Patients</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">{{ "{:.2f}%".format(readmission_rate) }}</div>
            <div class="kpi-label">30-Day Readmission Rate</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">{{ "{:,}".format(readmitted_count) }}</div>
            <div class="kpi-label">30-Day Readmissions</div>
        </div>
    </div>

    <h2>2. Readmission Outcome Definition</h2>
    <p>
        The primary endpoint is defined as <strong>unplanned hospital readmission within 30 days</strong> of discharge. In the encounter records:
    </p>
    <ul>
        <li><strong>Positive (1):</strong> Encounters recorded with outcome <code>&lt;30</code> (readmitted within 30 days).</li>
        <li><strong>Negative (0):</strong> Encounters recorded with outcome <code>&gt;30</code> (readmitted after 30 days) or <code>NO</code> (no recorded readmission).</li>
    </ul>

    <h2>3. Data Quality & Cleaning Summary</h2>
    <p>
        Data quality audit performed on initial ingestion:
    </p>
    <ul>
        <li><strong>Exact Duplicate Records:</strong> {{ exact_duplicates }} identical rows removed.</li>
        <li><strong>Missing Values:</strong> {{ columns_with_missing }} column(s) exhibited missing or sentinel values (e.g. <code>?</code>).</li>
        <li><strong>Cleaning Operations:</strong> {{ cleaning_ops_count }} discrete auditable transformations applied.</li>
    </ul>

    {% if top_missing_table %}
    <h3>Top Incomplete Variables</h3>
    <table>
        <thead>
            <tr>
                <th>Column</th>
                <th>Missing Count</th>
                <th>Missing Rate</th>
            </tr>
        </thead>
        <tbody>
            {% for row in top_missing_table %}
            <tr>
                <td><code>{{ row.column }}</code></td>
                <td>{{ "{:,}".format(row.total_missing) }}</td>
                <td>{{ "{:.1f}%".format(row.missing_percentage) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}

    <h2>4. Key Readmission Associations (Bivariate Analysis)</h2>
    {% if associations_table %}
    <table>
        <thead>
            <tr>
                <th>Variable / Category</th>
                <th>Sample Size</th>
                <th>30-Day Readmission Rate</th>
                <th>95% Confidence Interval</th>
            </tr>
        </thead>
        <tbody>
            {% for row in associations_table %}
            <tr>
                <td>{{ row.category }}</td>
                <td>{{ "{:,}".format(row.total_encounters) }}</td>
                <td><strong>{{ "{:.2f}%".format(row.readmission_rate_pct) }}</strong></td>
                <td>[{{ "{:.2f}%".format(row.ci_lower_pct) }} - {{ "{:.2f}%".format(row.ci_upper_pct) }}]</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}

    <h2>5. Statistical Hypothesis Testing</h2>
    {% if statistical_tests %}
    <table>
        <thead>
            <tr>
                <th>Hypothesis Test</th>
                <th>Variable</th>
                <th>Test Statistic</th>
                <th>Raw p-value</th>
                <th>FDR Adjusted p</th>
                <th>Effect Size</th>
            </tr>
        </thead>
        <tbody>
            {% for test in statistical_tests %}
            <tr>
                <td>{{ test.test_name }}</td>
                <td><code>{{ test.variable }}</code></td>
                <td>{{ test.statistic if test.statistic is defined else test.chi2_stat }}</td>
                <td>{{ "{:.2e}".format(test.p_value) }}</td>
                <td>{{ "{:.2e}".format(test.fdr_adjusted_p) if test.fdr_adjusted_p is defined else "N/A" }}</td>
                <td>{{ test.effect_size if test.effect_size is defined else test.cramers_v }} ({{ test.effect_size_label if test.effect_size_label is defined else test.effect_size_metric }})</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}

    <h2>6. Methodological Limitations & Confounding</h2>
    <ul>
        <li><strong>Unmeasured Confounders:</strong> Crucial determinants of readmission (socioeconomic status, functional independence, post-discharge medication adherence, caregiver support) are not captured in the encounter records.</li>
        <li><strong>Dataset Censoring:</strong> Encounters resulting in readmission to an unpartnered hospital system appear as non-readmissions (right censoring).</li>
        <li><strong>Exploratory Status:</strong> Statistical significance does not indicate clinical magnitude or causal reversibility. Interventions targeting associated markers must be evaluated in prospective trials.</li>
    </ul>

    <footer>
        Hospital Readmission Intelligence Platform &bull; Reproducible Healthcare Analytics &bull; Generated {{ generated_at }}
    </footer>
</div>
</body>
</html>
"""


class ReportGenerator:
    """Generates standardized HTML and PDF analytical reports."""

    def __init__(self, output_dir: str | Path = "reports/generated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_report(
        self,
        report_data: dict[str, Any],
        filename: str = "readmission_analytical_report.html",
    ) -> Path:
        """Renders HTML analytical report using Jinja2."""
        template = Template(HTML_TEMPLATE)

        # Inject standard defaults
        data = {
            "version": __version__,
            "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
            **report_data,
        }

        html_content = template.render(**data)
        out_path = self.output_dir / filename
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info("Generated HTML report at %s", out_path)
        return out_path

    def generate_pdf_report(
        self,
        report_data: dict[str, Any],
        filename: str = "readmission_analytical_report.pdf",
    ) -> Path:
        """Generates PDF analytical report using ReportLab."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        except ImportError as e:
            logger.warning("ReportLab is not installed or unavailable: %s", e)
            raise RuntimeError("PDF generation requires reportlab package.") from e

        out_path = self.output_dir / filename
        doc = SimpleDocTemplate(str(out_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            alignment=0,
        )
        heading_style = ParagraphStyle(
            "DocHeading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0284c7"),
            spaceBefore=14,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#1e293b"),
        )
        disclaimer_style = ParagraphStyle(
            "DocDisclaimer",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#991b1b"),
        )

        story.append(Paragraph("Hospital Readmission Intelligence Platform", title_style))
        story.append(Paragraph(f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')} | Platform v{__version__}", body_style))
        story.append(Spacer(1, 10))

        # Disclaimer box
        disc_text = (
            "<b>Exploratory Clinical Disclaimer:</b> This report presents retrospective statistical associations. "
            "Findings do not establish clinical causality or constitute a validated prognostic prediction system."
        )
        t_disc = Table([[Paragraph(disc_text, disclaimer_style)]], colWidths=[540])
        t_disc.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff1f2")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#f43f5e")),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(t_disc)
        story.append(Spacer(1, 12))

        # KPI Metrics Table
        story.append(Paragraph("1. Executive Summary & KPIs", heading_style))
        kpi_data = [
            ["Metric", "Value"],
            ["Total Encounters", f"{report_data.get('total_encounters', 0):,}"],
            ["Unique Patients", f"{report_data.get('unique_patients', 0):,}" if report_data.get('unique_patients') else "N/A"],
            ["30-Day Readmissions", f"{report_data.get('readmitted_count', 0):,}"],
            ["30-Day Readmission Rate", f"{report_data.get('readmission_rate', 0.0):.2f}%"],
            ["Cleaned Rows", f"{report_data.get('total_encounters', 0):,}"],
        ]
        t_kpi = Table(kpi_data, colWidths=[250, 290])
        t_kpi.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        story.append(t_kpi)
        story.append(Spacer(1, 14))

        # Outcome Definition
        story.append(Paragraph("2. Readmission Outcome Definition", heading_style))
        story.append(Paragraph(
            "Primary outcome is 30-day readmission defined by encounter label '<30' = 1, "
            "with '>30' and 'NO' binarized to 0. Retrospective recording without clinical extrapolation.",
            body_style,
        ))
        story.append(Spacer(1, 10))

        # Group Rates Table
        story.append(Paragraph("3. Readmission Rate by Primary Groups", heading_style))
        assoc = report_data.get("associations_table", [])
        if assoc:
            t_assoc_data = [["Category", "Encounters", "30d Readmission Rate", "95% Wilson CI"]]
            for row in assoc[:10]:
                t_assoc_data.append([
                    str(row.get("category", "")),
                    f"{row.get('total_encounters', 0):,}",
                    f"{row.get('readmission_rate_pct', 0.0):.2f}%",
                    f"[{row.get('ci_lower_pct', 0.0):.2f}%, {row.get('ci_upper_pct', 0.0):.2f}%]",
                ])
            t_assoc = Table(t_assoc_data, colWidths=[180, 110, 120, 130])
            t_assoc.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]))
            story.append(t_assoc)

        story.append(Spacer(1, 14))
        story.append(Paragraph("4. Methodological Limitations", heading_style))
        story.append(Paragraph(
            "Findings reflect single-system retrospective electronic records. Unmeasured determinants such as "
            "post-discharge social determinants of health and out-of-network care transitions are unobserved.",
            body_style,
        ))

        doc.build(story)
        logger.info("Generated PDF report at %s", out_path)
        return out_path
