# core/recommender.py
from typing import List
import pandas as pd
from .schemas import InvestorProfile, Recommendation, RiskProfile, InvestmentPurpose
from .config import PRODUCT_CATALOG_PATH

_product_df_cache: pd.DataFrame | None = None

def load_product_catalog() -> pd.DataFrame:
    global _product_df_cache
    if _product_df_cache is None:
        df = pd.read_csv(PRODUCT_CATALOG_PATH)
        _product_df_cache = df
    return _product_df_cache

def infer_risk_profile(final_risk_score: float) -> RiskProfile:
    if final_risk_score <= 20:
        return "Defensive"
    if final_risk_score <= 40:
        return "Conservative"
    if final_risk_score <= 60:
        return "Balanced"
    if final_risk_score <= 80:
        return "Growth"
    return "Aggressive"

def simple_risk_score(profile: InvestorProfile) -> float:
    # Very simple example: weight term & tolerance & budget
    term_factor = min(profile.investment_term_months / 360, 1.0) * 100
    tol_factor = (profile.risk_tolerance - 1) / 4 * 100
    # budget factor (higher investable -> slightly higher capacity)
    budget_factor = min(profile.investment_budget / 100000, 1.0) * 100

    return 0.5 * tol_factor + 0.3 * term_factor + 0.2 * budget_factor

def recommend_products(profile: InvestorProfile, top_n: int = 5) -> List[Recommendation]:
    df = load_product_catalog().copy()

    score = simple_risk_score(profile)
    risk_profile = infer_risk_profile(score)

    # Filter by risk profile
    df = df[df["Suitable_Risk_Profiles"].str.contains(risk_profile)]

    # Filter by purpose where possible
    purpose = profile.investment_purpose
    df_purpose = df[df["Suitable_Purposes"].str.contains(purpose)]
    if not df_purpose.empty:
        df = df_purpose

    # Basic ranking: closer risk level to tolerance, and affordable
    df["affordable"] = profile.investment_budget >= df["Min_Investment"]
    df["risk_diff"] = (df["Risk_Level"] - profile.risk_tolerance).abs()
    df = df.sort_values(["affordable", "risk_diff", "Min_Investment"],
                        ascending=[False, True, True])

    recs: List[Recommendation] = []
    for _, row in df.head(top_n).iterrows():
        recs.append(
            Recommendation(
                product_name=row["Product_Name"],
                product_type=row["Product_Type"],
                risk_level=int(row["Risk_Level"]),
                min_term_months=int(row["Min_Term_Months"]),
                min_investment=float(row["Min_Investment"]),
                expected_return_pct=float(row["Expected_Annual_Return_pct"])
                if "Expected_Annual_Return_pct" in row and not pd.isna(row["Expected_Annual_Return_pct"])
                else None,
            )
        )
    return recs
