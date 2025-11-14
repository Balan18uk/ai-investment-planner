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
    Very simple illustrative risk score:
    - term (longer) increases capacity
    - risk_tolerance is main driver
    - budget gives a small extra capacity boost
    - investing more than current savings (leverage) increases risk
    """
    # Base components
    term_factor = min(profile.investment_term_months / 360, 1.0) * 100
    tol_factor = (profile.risk_tolerance - 1) / 4 * 100
    budget_factor = min(profile.investment_budget / 100000, 1.0) * 100

    base_score = 0.5 * tol_factor + 0.3 * term_factor + 0.2 * budget_factor

    # Extra risk if investing more than savings (leverage behaviour)
    leverage_boost = 0.0
    if profile.investment_budget > profile.savings:
        # How much bigger the investment is than savings
        leverage_ratio = (profile.investment_budget - profile.savings) / max(
            profile.savings, 1.0
        )
        # Cap the effect so it does not explode
        leverage_boost = min(leverage_ratio * 20.0, 20.0)

    score = base_score + leverage_boost

    # Keep score in 0 to 100 range
    return max(0.0, min(score, 100.0))



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


def recommend_products(profile: InvestorProfile, top_n: int = 5) -> List[Recommendation]:
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
    df["purpose_match"] = df["Suitable_Purposes"].str.contains(profile.investment_purpose)

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
                expected_return_pct=float(row["Expected_Annual_Return_pct"])
                if "Expected_Annual_Return_pct" in row
                and not pd.isna(row["Expected_Annual_Return_pct"])
                else None,
            )
        )

    return recs
