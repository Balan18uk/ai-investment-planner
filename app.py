# app.py
import streamlit as st
from core.config import OPENAI_API_KEY
from core.llm_extractor import extract_profile
from core.recommender import recommend_products, simple_risk_score, infer_risk_profile

st.set_page_config(page_title="AI Investment Planner", layout="centered")

st.title("💼 AI Investment Planner")
st.write("Describe your client's financial situation and goals below:")

if not OPENAI_API_KEY:
    st.error("❌ OPENAI_API_KEY is missing. Please check your .env file.")
else:
    st.success("✅ OpenAI API key loaded.")

user_text = st.text_area("📝 Client profile and goals:", height=200)

if st.button("Analyze and recommend"):
    if not user_text.strip():
        st.warning("Please enter some details about the client.")
        st.stop()

    with st.spinner("Analyzing profile with AI..."):
        try:
            profile = extract_profile(user_text)
        except Exception as e:
            st.error(f"Failed to extract profile: {e}")
            st.stop()

    st.subheader("📋 Extracted profile")
    st.json(profile.__dict__)

    score = simple_risk_score(profile)
    risk_profile = infer_risk_profile(score)

    st.info(f"🔍 Risk score: {score:.1f} → Profile: **{risk_profile}**")

    recs = recommend_products(profile)
    if recs:
        st.subheader("🎯 Recommended investment products")
        for r in recs:
            st.markdown(
                f"**{r.product_name}** "
                f"({r.product_type})  \n"
                f"- Risk level: {r.risk_level}  \n"
                f"- Min term: {r.min_term_months} months  \n"
                f"- Min investment: £{r.min_investment:,.0f}"
            )
    else:
        st.warning("No suitable products found for this profile.")
