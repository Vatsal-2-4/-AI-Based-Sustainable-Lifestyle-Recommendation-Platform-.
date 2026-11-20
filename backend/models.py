"""Validated profile data passed from UI to calculation services."""
from dataclasses import dataclass

@dataclass
class LifestyleProfile:
    city: str
    housing_type: str
    commute_km_week: float
    diet_pattern: str
    electricity_kwh_month: float
    monthly_budget_inr: float = 0.0
