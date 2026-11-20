"""Documented activity-based household footprint estimates.

Water and waste activity are reported as physical indicators only: no generic
India-specific household factors are applied to those categories.
"""
from pathlib import Path
import math
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
FACTOR_PATH=ROOT/"dataset"/"emission_factors.csv"
FOOD_FACTOR_PATH=ROOT/"dataset"/"food_emission_factors.csv"
FACTOR_VERSION="CEA23-24-IPCC06-OWID18-v1"

def load_factors():
    factors=pd.read_csv(FACTOR_PATH).fillna("")
    food=pd.read_csv(FOOD_FACTOR_PATH).fillna("")
    if factors["factor_id"].duplicated().any() or food["food_key"].duplicated().any():
        raise ValueError("Emission factor identifiers must be unique")
    return factors,food

def _nonnegative(value,label):
    try: number=float(value)
    except (TypeError,ValueError) as exc: raise ValueError(f"{label} must be a number") from exc
    if not math.isfinite(number) or number<0: raise ValueError(f"{label} must be a finite, non-negative number")
    return number

def calculate_footprint(inputs):
    """Return annual kg CO2e estimates plus non-GHG water/waste indicators.

    Inputs: monthly litres petrol/diesel, monthly electricity kWh, weekly kg
    per food group, per-person water litres/day, and weekly waste kg by stream.
    """
    factors,food_factors=load_factors()
    indexed=factors.set_index("factor_id")
    def factor(fid): return float(indexed.loc[fid,"factor_value"])
    petrol_l=_nonnegative(inputs.get("petrol_l_month",0),"Petrol litres per month")*12
    diesel_l=_nonnegative(inputs.get("diesel_l_month",0),"Diesel litres per month")*12
    petrol_kg_l=factor("PETROL_IPCC_EF")*factor("PETROL_IPCC_NCV")*factor("PETROL_DENSITY")/1_000_000
    diesel_kg_l=factor("DIESEL_IPCC_EF")*factor("DIESEL_IPCC_NCV")*factor("DIESEL_DENSITY")/1_000_000
    transport=petrol_l*petrol_kg_l+diesel_l*diesel_kg_l
    electricity=_nonnegative(inputs.get("electricity_kwh_month",0),"Electricity kWh per month")*12*factor("ELEC_IN_CEA_2023_24")
    weekly_food=inputs.get("food_kg_week",{})
    if not isinstance(weekly_food,dict): raise ValueError("Food entries must be supplied as a mapping")
    food_index=food_factors.set_index("food_key")
    food_total=0.0; food_breakdown={}
    for key,amount in weekly_food.items():
        if key not in food_index.index: raise ValueError(f"Unknown food factor: {key}")
        annual_kg=_nonnegative(amount,f"{key} kg per week")*52
        emission=annual_kg*float(food_index.loc[key,"kg_co2e_per_kg_product"])
        food_total+=emission
        if emission: food_breakdown[str(food_index.loc[key,"food_label"])]=round(emission,2)
    water_l_year=_nonnegative(inputs.get("water_l_person_day",0),"Water litres per person per day")*365
    waste_week=inputs.get("waste_kg_week",{})
    if not isinstance(waste_week,dict): raise ValueError("Waste entries must be supplied as a mapping")
    waste_kg_year={str(k):round(_nonnegative(v,f"{k} waste kg per week")*52,2) for k,v in waste_week.items()}
    categories={"Transportation":round(transport,2),"Electricity":round(electricity,2),"Food":round(food_total,2)}
    return {
        "total_kg_co2e":round(sum(categories.values()),2),
        "category_kg_co2e":categories,
        "food_breakdown_kg_co2e":food_breakdown,
        "water_litres_year":round(water_l_year,1),
        "waste_kg_year":waste_kg_year,
        "transport_factor_kg_co2_per_litre":{"petrol":round(petrol_kg_l,4),"diesel":round(diesel_kg_l,4)},
        "factor_version":FACTOR_VERSION,
    }

def source_summary():
    return load_factors()
