
# © 2025 TrueVizion Hub Ltd. All rights reserved.
# Proprietary and confidential. Unauthorized use is prohibited.

import json
from openai import OpenAI

from .schemas import InvestorProfile
from .config import OPENAI_API_KEY, OPENAI_MODEL
from .mappings import INCOME_BANDS, DEBT_BANDS, PURPOSES

client = OpenAI(api_key=OPENAI_API_KEY)


def infer_income_bracket(annual_income: float | None) -> str:
    """
    Map a numeric annual income to one of the configured income bands.
    Falls back to the lowest band if income is missing.
    """
    if annual_income is None:
        return INCOME_BANDS[0]  # default to lowest band

    # Adjust thresholds and labels to match your INCOME_BANDS exactly
    if annual_income < 25_000:
        return "0-£25,000"
    elif annual_income < 50_000:
        return "25,000 - 49,999"
    elif annual_income < 75_000:
        return "50,000 - 74,999"
    elif annual_income < 100_000:
        return "75,000 - 99,999"
    else:
        return "100,000 or more"


def extract_profile(user_text: str) -> InvestorProfile:
    system = (
        "You are a strict JSON extraction engine. "
        "Return ONLY valid JSON with the specified schema. No extra text."
    )

    user = f"""
Extract an investor profile from the text.

Step 1: infer the client's ANNUAL income in GBP. If the text gives a monthly or weekly amount, convert it to annual.
Examples:
- "5,000 per month" -> annual_income_gbp = 60000
- "800 per week" -> annual_income_gbp ≈ 41600

Allowed categorical values:
- debt_level: one of {DEBT_BANDS}
- investment_purpose: one of {PURPOSES}

Also extract numeric fields (all in GBP unless stated otherwise):
- annual_income_gbp (number, per year, after conversion if needed)
- savings (number)
- investment_budget (number)
- investment_term_months (integer, best estimate if not stated)
- risk_tolerance (integer 1-5)

Return ONLY valid JSON with these fields:
{{
  "annual_income_gbp": 0,
  "savings": 0,
  "debt_level": "...",
  "investment_budget": 0,
  "investment_term_months": 0,
  "risk_tolerance": 1,
  "investment_purpose": "..."
}}

User text:
\"\"\"{user_text}\"\"\" 
"""

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0,
        max_tokens=250,
    )

    raw = resp.choices[0].message.content.strip()

    # Try direct JSON first
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"Model did not return JSON: {raw}")
        data = json.loads(raw[start : end + 1])

    # Extract numeric annual income and infer bracket
    annual_income = data.get("annual_income_gbp", 0) or 0
    income_bracket = infer_income_bracket(float(annual_income))

    return InvestorProfile(
        income_bracket=income_bracket,
        savings=float(data.get("savings", 0) or 0),
        debt_level=data.get("debt_level", "No debt"),
        investment_budget=float(data.get("investment_budget", 0) or 0),
        investment_term_months=int(data.get("investment_term_months", 60) or 60),
        risk_tolerance=int(data.get("risk_tolerance", 3) or 3),
        investment_purpose=data.get("investment_purpose", "Wealth accumulation"),  # type: ignore
    )
