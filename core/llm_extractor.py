# © 2025 TrueVizion Hub Ltd. All rights reserved.
# Proprietary and confidential. Unauthorized use is prohibited.


import json
from openai import OpenAI
from .schemas import InvestorProfile, InvestmentPurpose
from .config import OPENAI_API_KEY, OPENAI_MODEL
from .mappings import INCOME_BANDS, DEBT_BANDS, PURPOSES

client = OpenAI(api_key=OPENAI_API_KEY)

def extract_profile(user_text: str) -> InvestorProfile:
    system = (
        "You are a strict JSON extraction engine. "
        "Return ONLY valid JSON with the specified schema. No extra text."
    )

    user = f"""
Extract an investor profile from the text.

Allowed values:
- income_bracket: one of {INCOME_BANDS}
- debt_level: one of {DEBT_BANDS}
- investment_purpose: one of {PURPOSES}

Also extract:
- savings (number, £)
- investment_budget (number, £)
- investment_term_months (integer)
- risk_tolerance (integer 1-5)

Return JSON:
{{
  "income_bracket": "...",
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
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
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
        data = json.loads(raw[start:end+1])

    return InvestorProfile(
        income_bracket=data["income_bracket"],
        savings=float(data["savings"]),
        debt_level=data["debt_level"],
        investment_budget=float(data["investment_budget"]),
        investment_term_months=int(data["investment_term_months"]),
        risk_tolerance=int(data["risk_tolerance"]),
        investment_purpose=data["investment_purpose"],  # type: ignore
    )
