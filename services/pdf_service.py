"""
services/pdf_service.py — PDF report generation for the Dashboard page.

build_pdf_report() is the only public symbol. It takes pre-computed
aggregates and returns raw PDF bytes suitable for st.download_button.
"""

import os
from datetime import datetime

from fpdf import FPDF

from core.db_dashboard import fmt_ugx

LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "URA-logo.png")


def build_pdf_report(
    total_tax, total_net, total_records, effective_rate, insight_text, filters_desc,
    category_summary, fy_summary, sample
):
    pdf = FPDF()
    pdf.add_page()

    if os.path.exists(LOGO_PATH):
        pdf.image(LOGO_PATH, x=10, y=8, w=22)

    pdf.set_xy(38, 10)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(27, 79, 156)
    pdf.cell(0, 8, "URA Tax Invoice Dashboard - Report", ln=True)

    pdf.set_xy(38, 18)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(90, 107, 135)
    pdf.cell(0, 6, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)

    pdf.ln(18)
    pdf.set_draw_color(255, 209, 0)
    pdf.set_line_width(1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(13, 46, 99)
    pdf.cell(0, 7, "Applied Filters", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 5.5, filters_desc)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(13, 46, 99)
    pdf.cell(0, 7, "Key Metrics", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    metrics = [
        ("Total Tax Deducted", fmt_ugx(total_tax)),
        ("Total Net Amount", fmt_ugx(total_net)),
        ("Total Records", f"{total_records:,}"),
        ("Effective Tax Rate", f"{effective_rate:.1f}%"),
    ]
    for label, value in metrics:
        pdf.cell(70, 6.5, label, border=0)
        pdf.cell(0, 6.5, value, border=0, ln=True)
    pdf.ln(2)

    if insight_text:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_fill_color(255, 248, 222)
        pdf.set_text_color(13, 46, 99)
        pdf.multi_cell(0, 6, f"Insight: {insight_text}", fill=True)
        pdf.ln(2)

    def add_table(title, summary_df, label_col, value_col):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(13, 46, 99)
        pdf.cell(0, 7, title, ln=True)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(27, 79, 156)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(90, 6.5, label_col.replace("_", " ").title(), border=1, fill=True)
        pdf.cell(0, 6.5, "Tax Deducted (UGX)", border=1, fill=True, ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(30, 30, 30)
        for _, r in summary_df.iterrows():
            pdf.cell(90, 6, str(r[label_col]), border=1)
            pdf.cell(0, 6, f"{float(r[value_col]):,.2f}", border=1, ln=True)
        pdf.ln(4)

    add_table("Tax Deducted by Category", category_summary, "tax_category", "tax_amount")
    add_table("Tax Deducted by Financial Year", fy_summary, "financial_year", "tax_amount")

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(13, 46, 99)
    pdf.cell(0, 7, "Sample Records (most recent 15 of filtered selection)", ln=True)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(27, 79, 156)
    pdf.set_text_color(255, 255, 255)
    col_widths = [40, 35, 35, 35, 35]
    headers = ["Invoice ID", "Category", "Net Amount", "Tax Amount", "Effective Date"]
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 6.5, h, border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(30, 30, 30)
    for _, row in sample.iterrows():
        pdf.cell(col_widths[0], 6, str(row["invoice_id"]), border=1)
        pdf.cell(col_widths[1], 6, str(row["tax_category"]), border=1)
        pdf.cell(col_widths[2], 6, f"{row['net_amount']:,.0f}", border=1)
        pdf.cell(col_widths[3], 6, f"{row['tax_amount']:,.0f}", border=1)
        pdf.cell(col_widths[4], 6, str(row["effective_date"]), border=1)
        pdf.ln()

    return bytes(pdf.output())
