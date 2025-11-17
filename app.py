# © 2025 TrueVizion Hub Ltd. All rights reserved.
# Proprietary and confidential. Unauthorized use is prohibited.

import streamlit as st

from core.config import OPENAI_API_KEY
from core.llm_extractor import extract_profile
from core.mappings import INCOME_BANDS, DEBT_BANDS, PURPOSES
from core.schemas import InvestorProfile
from core.cards import make_product_card_html
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


# Header with logo and title
col_logo, col_title = st.columns([1, 4])

with col_logo:
    st.image("assets/truevizion_logo.png", use_container_width=True)

with col_title:
    st.title("💼 AI Investment Planner")
    st.write(
        "TrueVizion Hub – AI-assisted investment profiling and product suggestions."
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
            principal = final_profile.investment_budget
            months = final_profile.investment_term_months

            # ----- Best match (first product, full width) -----
            best = recommendations[0]

            # Optional: show a Streamlit badge above the card
            #st.badge("Best match", color="green")

            best_html = make_product_card_html(
                best,
                principal=principal,
                term_months=months,
                label="Best match",
                highlight=True,  # uses bg_best
            )
            st.markdown(best_html, unsafe_allow_html=True)

            # ----- Alternative options (two columns) -----
            if len(recommendations) > 1:
                st.markdown("#### Alternative options")
                col1, col2 = st.columns(2)

                for i, rec in enumerate(recommendations[1:]):
                    html = make_product_card_html(
                        rec,
                        principal=principal,
                        term_months=months,
                        label="Alternative option",
                        highlight=False,  # uses bg_alt
                    )
                    target_col = col1 if i % 2 == 0 else col2
                    with target_col:
                        st.markdown(html, unsafe_allow_html=True)

            # PDF generation as before...              

            # (PDF generation stays exactly as you have it)
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


