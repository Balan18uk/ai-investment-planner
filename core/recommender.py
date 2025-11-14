# core/recommender.py

import pandas as pd
from typing import List

from .schemas import InvestorProfile, Recommendation
from .config import PRODUCT_CATALOG_PATH

_product_df_cache: pd.DataFrame | None = None


def load_product_catalog() -> pd.DataFrame:
    """Load product catalogue once and cache it."""
    global _product_df_cache
    if _product_df_cache is None:
        _product_df_cache = pd.read_csv(PRODUCT_CATALOG_PATH)
    return _product_df_cache


def simple_risk_score(profile: InvestorProfile) -> float:
    """
    Professional-grade risk scoring model combining:
    - risk tolerance
    - risk capacity
    - financial stability
    - time horizon
    - knowledge & experience
    - leverage behaviour
    """

    income = (
        20000 if profile.income_bracket == "0 - No income / rely on investment returns"
        else 30000 if profile.income_bracket == "0-£25,000"
        else 40000 if profile.income_bracket == "25,000 - 49,999"
        else 65000 if profile.income_bracket == "50,000 - 99,999"
        else 120000
    )

    # ---------- 1. RISK TOLERANCE ----------
    risk_tolerance_score = (profile.risk_tolerance - 1) / 4 * 100

    # ---------- 2. RISK CAPACITY ----------
    # Savings adequacy ratio (3-month rule)
    emergency_need = income / 4
    savings_ratio = profile.savings / max(emergency_need, 1)

    if savings_ratio < 0.5:
        savings_score = 20
    elif savings_ratio < 1:
        savings_score = 40
    elif savings_ratio < 2:
        savings_score = 60
    else:
        savings_score = 80

    # Debt ratio
    debt_value = (
        0 if profile.debt_level == "No debt" else
        5000 if profile.debt_level == "Less than 10,000" else
        15000 if profile.debt_level == "10,000 - 25,000" else
        30000
    )
    debt_ratio = debt_value / max(income, 1)

    if debt_ratio > 0.5:
        debt_score = 20
    elif debt_ratio > 0.25:
        debt_score = 40
    elif debt_ratio > 0.1:
        debt_score = 60
    else:
        debt_score = 80

    # Investment burden relative to savings
    if profile.investment_budget <= profile.savings:
        investment_burden_score = 80
    else:
        ratio = profile.investment_budget / max(profile.savings, 1)
        if ratio < 2:
            investment_burden_score = 60
        elif ratio < 5:
            investment_burden_score = 40
        else:
            investment_burden_score = 20

    capacity_score = (savings_score + debt_score + investment_burden_score) / 3

    # ---------- 3. TIME HORIZON ----------
    time_score = min(profile.investment_term_months / 360, 1.0) * 100

    # ---------- 4. FINANCIAL STABILITY ----------
    financial_stability_score = (savings_score + debt_score) / 2

    # ---------- 5. KNOWLEDGE & EXPERIENCE ----------
    knowledge_score = 50  # default until you add question

    # ---------- 6. LEVERAGE PENALTY ----------
    if profile.investment_budget > profile.savings:
        leverage_ratio = profile.investment_budget / max(profile.savings, 1)
        leverage_penalty = min((leverage_ratio - 1) * 20, 30)
    else:
        leverage_penalty = 0

    # ---------- Final Weighted Score ----------
    final_score = (
        0.30 * risk_tolerance_score +
        0.20 * capacity_score +
        0.20 * time_score +
        0.15 * financial_stability_score +
        0.10 * knowledge_score -
        0.05 * leverage_penalty
    )

    return max(0.0, min(final_score, 100.0))


def infer_risk_profile(score: float) -> str:
    """
    Map numeric score 0–100 into a risk profile label.
    """
    if score <= 20:
        return "Defensive"
    if score <= 40:
        return "Conservative"
    if score <= 60:
        return "Balanced"
    if score <= 80:
        return "Growth"
    return "Aggressive"


def recommend_products(
    profile: InvestorProfile, top_n: int = 5
) -> List[Recommendation]:
    """
    Recommend up to top_n products using a two-stage logic:

    1) Hard filter on risk profile suitability.
    2) Rank by affordability, risk distance, and min investment.
    3) First take products matching the investment purpose.
    4) If fewer than top_n, fill remaining slots from other suitable products.
    """
    df = load_product_catalog().copy()

    # 1) Work out risk profile from numeric score
    score = simple_risk_score(profile)
    risk_profile = infer_risk_profile(score)

    # 2) Hard filter by risk profile (appropriateness)
    df = df[df["Suitable_Risk_Profiles"].str.contains(risk_profile)]

    if df.empty:
        return []

    # 3) Basic ranking features
    df["affordable"] = profile.investment_budget >= df["Min_Investment"]
    df["risk_diff"] = (df["Risk_Level"] - profile.risk_tolerance).abs()

    # 4) Purpose match flag (soft filter)
    df["purpose_match"] = df["Suitable_Purposes"].str.contains(
        profile.investment_purpose
    )

    # ---------- Stage 1: products that match the purpose ----------
    df_purpose = df[df["purpose_match"]]

    df_purpose = df_purpose.sort_values(
        ["affordable", "risk_diff", "Min_Investment"],
        ascending=[False, True, True],
    )

    selected = df_purpose.head(top_n)

    # ---------- Stage 2: if we have fewer than top_n, fill from others ----------
    if len(selected) < top_n:
        remaining = df[~df.index.isin(selected.index)]
        remaining = remaining.sort_values(
            ["affordable", "risk_diff", "Min_Investment"],
            ascending=[False, True, True],
        )

        needed = top_n - len(selected)
        extra = remaining.head(needed)
        selected = pd.concat([selected, extra])

    recs: List[Recommendation] = []
    for _, row in selected.iterrows():
        recs.append(
            Recommendation(
                product_name=row["Product_Name"],
                product_type=row["Product_Type"],
                risk_level=int(row["Risk_Level"]),
                min_term_months=int(row["Min_Term_Months"]),
                min_investment=float(row["Min_Investment"]),
                expected_return_pct=(
                    float(row["Expected_Annual_Return_pct"])
                    if "Expected_Annual_Return_pct" in row
                    and not pd.isna(row["Expected_Annual_Return_pct"])
                    else None
                ),
            )
        )

    return recs
