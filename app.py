# © 2025 TrueVizion Hub Ltd. All rights reserved.
# Proprietary and confidential. Unauthorized use is prohibited.

import streamlit as st

from core.config import OPENAI_API_KEY
from core.llm_extractor import extract_profile
from core.mappings import INCOME_BANDS, DEBT_BANDS, PURPOSES
from core.schemas import InvestorProfile
from core.recommender import (
    simple_risk_score,
    infer_risk_profile,
    recommend_products,
)
from core.report import build_pdf_report


# --------------------------------------------------
# Streamlit page setup
# --------------------------------------------------
st.set_page_config(
    page_title="AI Investment Planner",
    layout="centered",
)

st.title("💼 AI Investment Planner")
st.write(
    "Describe your client's financial situation and goals in natural language. "
    "The AI will draft a profile, then you can review and complete it before "
    "getting recommendations."
)

# --------------------------------------------------
# API key status (only show if missing)
# --------------------------------------------------
if not OPENAI_API_KEY:
    st.error("❌ OpenAI API key missing. Please add it to your .env file.")

# --------------------------------------------------
# Session state initialisation
# --------------------------------------------------
if "ai_profile" not in st.session_state:
    st.session_state.ai_profile = None

# --------------------------------------------------
# Session state initialisation
# --------------------------------------------------
if "ai_profile" not in st.session_state:
    st.session_state.ai_profile = None

if "reset" not in st.session_state:
    st.session_state.reset = False

# Handle reset – this must run before widgets are created
if st.session_state.reset:
    st.session_state.user_text = ""
    st.session_state.ai_profile = None
    st.session_state.reset = False


# --------------------------------------------------
# Free text input
# --------------------------------------------------
user_text = st.text_area(
    "📝 Client profile and goals:",
    height=180,
    placeholder=(
        "Example: The client wants to invest for a house deposit in 5 years. "
        "He earns £45,000 per year, has £10,000 savings, no debt, and is "
        "cautious about risk."
    ),
    key="user_text",  
)

analyze_clicked = st.button("Analyze profile with AI")

# --------------------------------------------------
# 1) Analyse button: call LLM and store result in session_state
# --------------------------------------------------
if analyze_clicked:
    if not user_text.strip():
        st.warning("Please enter some information about the client first.")
    else:
        with st.spinner("Analysing profile with AI..."):
            try:
                ai_profile = extract_profile(user_text)
                st.session_state.ai_profile = ai_profile
            except Exception as e:
                st.error(f"Failed to extract profile from text: {e}")
                st.session_state.ai_profile = None

# Pull current AI profile from session (may be None)
ai_profile = st.session_state.ai_profile

# --------------------------------------------------
# 2) If we have an AI profile, show it and the form
# --------------------------------------------------
if ai_profile is not None:
    st.subheader("📋 Extracted profile (AI draft)")
    st.json(ai_profile.__dict__)

    st.markdown(
        "Please review and complete the profile below. "
        "You can correct anything that the AI misunderstood."
    )

    with st.form("profile_form"):
        income = st.selectbox(
            "Income bracket",
            INCOME_BANDS,
            index=INCOME_BANDS.index(ai_profile.income_bracket)
            if ai_profile.income_bracket in INCOME_BANDS
            else 0,
        )

        savings = st.number_input(
            "Total savings (£)",
            min_value=0.0,
            value=float(ai_profile.savings) if ai_profile.savings > 0 else 0.0,
            step=1000.0,
        )

        debt_level = st.selectbox(
            "Debt level",
            DEBT_BANDS,
            index=DEBT_BANDS.index(ai_profile.debt_level)
            if ai_profile.debt_level in DEBT_BANDS
            else 0,
        )

        investment_budget = st.number_input(
            "Amount available to invest now (£)",
            min_value=0.0,
            value=(
                float(ai_profile.investment_budget)
                if ai_profile.investment_budget > 0
                else 0.0
            ),
            step=1000.0,
        )

        investment_term_months = st.number_input(
            "Investment term (months)",
            min_value=1,
            value=(
                int(ai_profile.investment_term_months)
                if ai_profile.investment_term_months > 0
                else 60
            ),
            step=6,
        )

        risk_tolerance = st.slider(
            "Risk tolerance (1 - very low, 5 - very high)",
            min_value=1,
            max_value=5,
            value=(
                int(ai_profile.risk_tolerance)
                if 1 <= ai_profile.risk_tolerance <= 5
                else 3
            ),
        )

        investment_purpose = st.selectbox(
            "Main investment purpose",
            PURPOSES,
            index=PURPOSES.index(ai_profile.investment_purpose)
            if ai_profile.investment_purpose in PURPOSES
            else 0,
        )

        submitted = st.form_submit_button("✅ Confirm profile and get recommendations")

    # --------------------------------------------------
    # 3) After confirmation - compute risk and recommend products
    # --------------------------------------------------
    if submitted:
        final_profile = InvestorProfile(
            income_bracket=income,
            savings=savings,
            debt_level=debt_level,
            investment_budget=investment_budget,
            investment_term_months=investment_term_months,
            risk_tolerance=risk_tolerance,
            investment_purpose=investment_purpose,
        )

        st.subheader("✅ Confirmed client profile")
        st.json(final_profile.__dict__)

        # Leverage warning
        if final_profile.investment_budget > final_profile.savings:
            st.warning(
                "⚠️ The amount to be invested is higher than current savings. "
                "This may involve borrowing or leverage and increases "
                "investment risk."
            )

        # Risk score and profile
        score = simple_risk_score(final_profile)
        risk_profile = infer_risk_profile(score)

        st.subheader("📊 Risk assessment")
        st.info(
            f"Risk score: **{score:.1f}**  \n"
            f"Assigned risk profile: **{risk_profile}**"
        )

        # Recommendations
        st.subheader("🎯 Recommended investment products")
        recommendations = recommend_products(final_profile)

        if recommendations:
            # Render product cards
            for idx, rec in enumerate(recommendations):
                # Decide styling: first = best match, others = alternatives
                if idx == 0:
                    # Best match - green-ish background
                    bg_colour = "#e6ffe6"
                    title = "🌟 Best match"
                else:
                    # Alternative options - light grey background
                    bg_colour = "#f5f5f5"
                    title = "Alternative option"

                principal = final_profile.investment_budget
                months = final_profile.investment_term_months

                # Build content lines (plain text, we will wrap in HTML)
                lines = [
                    f"<b>{rec.product_name}</b> ({rec.product_type})",
                    f"- Risk level: {rec.risk_level}",
                    f"- Minimum term: {rec.min_term_months} months",
                    f"- Minimum investment: £{rec.min_investment:,.0f}",
                ]

                # Indicative annual return and projection
                rate = getattr(rec, "expected_return_pct", None)
                if rate is not None:
                    lines.append(
                        f"- Indicative annual return: {rate:.1f}% "
                        "(illustrative only, not guaranteed)"
                    )

                    if principal >= rec.min_investment:
                        years = months / 12.0
                        r = rate / 100.0
                        future_value = principal * (1 + r) ** years
                        gain = future_value - principal

                        # Human-readable duration
                        if months < 24:
                            duration_text = f"{months} months"
                        else:
                            whole_years = months // 12
                            remaining_months = months % 12
                            if remaining_months == 0:
                                duration_text = f"{whole_years} years"
                            else:
                                duration_text = (
                                    f"{whole_years} years {remaining_months} months"
                                )

                        # Highlight projection sentence
                        projection_line = (
                            f"💡 <b>If you invest £{principal:,.0f} for "
                            f"{duration_text}, the projected value could be about "
                            f"£{future_value:,.0f} (gain of ~£{gain:,.0f}).</b>"
                        )
                        lines.append(projection_line)
                    else:
                        lines.append(
                            "- Client budget is below the minimum investment, "
                            "so projection is not shown."
                        )

                # Render card with background colour
                card_html = f"""
                <div style="background-color:{bg_colour}; padding:16px;
                            border-radius:10px; margin-bottom:12px;">
                    <div style="font-weight:600; margin-bottom:4px;">
                        {title}
                    </div>
                    <div>
                        {'<br>'.join(lines)}
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

            # Build PDF report and show download button
            pdf_bytes = build_pdf_report(
                profile=final_profile,
                risk_score=score,
                risk_profile=risk_profile,
                recommendations=recommendations,
            )

            st.download_button(
                label="📄 Download PDF report",
                data=pdf_bytes,
                file_name="investment_plan_report.pdf",
                mime="application/pdf",
            )

            st.caption(
                "Returns and projections are hypothetical and for demonstration "
                "purposes only. This app does not provide real financial advice "
                "or guaranteed outcomes."
            )
        else:
            st.warning(
                "No suitable products were found for this profile. "
                "You may want to adjust the inputs or product catalogue."
            )

# --------------------------------------------------
# Reset button - always visible
# --------------------------------------------------

st.markdown("---")
if st.button("🔄 Reset and start again"):
    st.session_state.reset = True
    st.rerun()


