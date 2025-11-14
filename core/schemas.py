# core/schemas.py
from dataclasses import dataclass
from typing import List, Literal

RiskProfile = Literal["Defensive", "Conservative", "Balanced", "Growth", "Aggressive"]
InvestmentPurpose = Literal[
    "Retirement savings",
    "Funding education",
    "Buying property",
    "Wealth accumulation",
]

@dataclass
class InvestorProfile:
    income_bracket: str
    savings: float
    debt_level: str
    investment_budget: float
    investment_term_months: int
    risk_tolerance: int
    investment_purpose: InvestmentPurpose

from dataclasses import dataclass
from typing import Optional

@dataclass
class Recommendation:
    product_name: str
    product_type: str
    risk_level: int
    min_term_months: int
    min_investment: float
    expected_return_pct: Optional[float] = None


    from dataclasses import dataclass
from typing import Optional



