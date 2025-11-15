from datetime import datetime
from typing import List

from fpdf import FPDF

from .schemas import InvestorProfile, Recommendation


class InvestmentReportPDF(FPDF):
    def header(self):
        # Logo
        try:
            # Adjust w (width) if needed; height will scale automatically
            self.image("assets/truevizion_logo.png", x=10, y=8, w=26)
        except Exception:
            pass

        # Title to the right of the logo
        self.set_xy(42, 10)  # x just to the right of the logo, y near top
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, "AI Investment Plan Summary", ln=1)

        # Timestamp under the title
        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 120)
        self.set_x(42)
        self.cell(
            0,
            6,
            f"Generated on {datetime.now().strftime('%d %b %Y %H:%M')}",
            ln=1,
        )

        # Reset colour and move cursor clearly below the logo/title area
        self.set_text_color(0, 0, 0)
        self.ln(10)  # add extra vertical space so body starts lower


def build_pdf_report(
    profile: InvestorProfile,
    risk_score: float,
    risk_profile: str,
    recommendations: List[Recommendation],
) -> bytes:
    """
    Build a formatted PDF summary for the investment plan.
    Returns PDF bytes suitable for Streamlit's download_button.
    """
    pdf = InvestmentReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf = InvestmentReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ---------- Section: Client Profile ----------
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Client Profile", ln=1)


    # ---------- Section: Client Profile ----------
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Client Profile", ln=1)
    pdf.set_font("Helvetica", "", 10)

    pdf.cell(0, 6, f"Income bracket: {profile.income_bracket}", ln=1)
    pdf.cell(0, 6, f"Savings: £{profile.savings:,.0f}", ln=1)
    pdf.cell(0, 6, f"Debt level: {profile.debt_level}", ln=1)
    pdf.cell(0, 6, f"Amount to invest now: £{profile.investment_budget:,.0f}", ln=1)
    pdf.cell(
        0,
        6,
        f"Investment term: {profile.investment_term_months} months",
        ln=1,
    )
    pdf.cell(0, 6, f"Risk tolerance (1-5): {profile.risk_tolerance}", ln=1)
    pdf.cell(0, 6, f"Investment purpose: {profile.investment_purpose}", ln=1)

    pdf.ln(4)

    # ---------- Section: Risk Assessment ----------
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Risk Assessment", ln=1)
    pdf.set_font("Helvetica", "", 10)

    pdf.cell(0, 6, f"Risk score: {risk_score:.1f}", ln=1)
    pdf.cell(0, 6, f"Assigned risk profile: {risk_profile}", ln=1)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(
        0,
        5,
        (
            "This risk profile is based on the client's risk tolerance, capacity for "
            "loss, time horizon, savings, debt level, and investment amount. It is "
            "illustrative and does not constitute regulated financial advice."
        ),
    )
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # ---------- Section: Recommended Products ----------
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Recommended Products", ln=1)
    pdf.set_font("Helvetica", "", 10)

    if not recommendations:
        pdf.cell(0, 6, "No suitable products were found for this profile.", ln=1)
    else:
        for idx, rec in enumerate(recommendations, start=1):
            # Product heading
            pdf.set_font("Helvetica", "B", 10)
            if idx == 1:
                heading = f"{idx}. {rec.product_name} (Best match)"
            else:
                heading = f"{idx}. {rec.product_name}"
            pdf.cell(0, 6, heading, ln=1)

            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 5, f"Type: {rec.product_type}", ln=1)
            pdf.cell(0, 5, f"Risk level: {rec.risk_level}", ln=1)
            pdf.cell(
                0,
                5,
                f"Minimum term: {rec.min_term_months} months",
                ln=1,
            )
            pdf.cell(
                0,
                5,
                f"Minimum investment: £{rec.min_investment:,.0f}",
                ln=1,
            )

            # Expected return, if present
            if getattr(rec, "expected_return_pct", None) is not None:
                pdf.cell(
                    0,
                    5,
                    f"Indicative annual return: {rec.expected_return_pct:.1f}% "
                    "(illustrative only, not guaranteed)",
                    ln=1,
                )

            pdf.ln(2)

    # ---------- Disclaimer ----------
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        0,
        4,
        (
            "Disclaimer: This report is generated by an AI-based prototype for "
            "demonstration purposes only. It does not constitute personal investment "
            "advice, a recommendation, or a suitability assessment under any "
            "regulatory framework."
        ),
    )
    pdf.set_text_color(0, 0, 0)

    # Return as bytes
# Return as bytes (fpdf2 already returns a bytes-like object)
    result = pdf.output(dest="S")
    pdf_bytes = bytes(result)
    return pdf_bytes

