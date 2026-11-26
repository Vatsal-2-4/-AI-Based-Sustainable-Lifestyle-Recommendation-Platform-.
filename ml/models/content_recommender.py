"""Content-based sustainable-action recommendation using TF-IDF and cosine similarity."""
from pathlib import Path
import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CATALOGUE_PATH = Path(__file__).resolve().parents[2] / "dataset" / "actions.csv"
REQUIRED_COLUMNS = {"action_id","category","title","description","match_terms","eligibility","impact_tier","cost_tier","difficulty","source_name","source_url"}
IMPACT_ORDER = {"low": 1, "medium": 2, "high": 3}

def preprocess_text(value):
    """Normalize text consistently for profile and catalogue documents."""
    value = str(value or "").casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def load_catalogue(path=CATALOGUE_PATH):
    """Read and validate the curated action dataset."""
    frame = pd.read_csv(path).fillna("")
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Action catalogue missing columns: {', '.join(sorted(missing))}")
    frame["difficulty"] = pd.to_numeric(frame["difficulty"], errors="raise")
    if frame["action_id"].duplicated().any():
        raise ValueError("Action IDs must be unique")
    if not frame["difficulty"].between(1, 5).all():
        raise ValueError("Action difficulty must be between 1 and 5")
    frame["document"] = frame.apply(lambda row: preprocess_text(" ".join(str(row[col]) for col in ("category","title","description","match_terms"))), axis=1)
    return frame

def _profile_document(profile):
    """Turn lifestyle responses into a text query plus explicit category signals."""
    parts=[]
    commute=preprocess_text(profile.get("commute", profile.get("commute_mode", "")))
    distance=float(profile.get("commute_km", profile.get("commute_km_day", 0)) or 0)
    days=int(profile.get("commute_days", profile.get("commute_days_week", 0)) or 0)
    if commute:
        parts.append(f"transport commute {commute}")
        if any(term in commute for term in ("petrol","diesel","car")): parts.append("private car vehicle driving fuel road trip")
        elif "two wheeler" in commute or "motorcycle" in commute: parts.append("scooter motorcycle petrol vehicle riding")
        elif any(term in commute for term in ("public transport","bus","metro")): parts.append("bus metro transit public transport route")
        elif "walk" in commute or "cycle" in commute: parts.append("walking bicycle cycling short active trips")
        elif "work from home" in commute: parts.append("remote work home based no regular commute")
    if distance >= 8 and days >= 3: parts.append("regular long commute frequent travel transport")
    elif distance > 0: parts.append("short commute local trips")
    electricity=float(profile.get("electricity", profile.get("electricity_kwh_month", 0)) or 0)
    if electricity >= 250: parts.append("high electricity consumption energy power bill appliances cooling")
    elif electricity > 0: parts.append("household electricity lighting appliances energy")
    ac=preprocess_text(profile.get("ac", profile.get("ac_usage", "")))
    if ac and ac not in {"rarely", "none"}: parts.append("air conditioner AC cooling electricity summer")
    diet=preprocess_text(profile.get("diet", profile.get("diet_pattern", "")))
    if diet: parts.append(f"food diet {diet} meals meat plant based food choices")
    water=preprocess_text(profile.get("water_usage", profile.get("shower_habit", "")))
    if water: parts.append(f"water usage {water} tap shower leak conservation reuse")
    waste=preprocess_text(profile.get("segregation", profile.get("waste_segregation", "")))
    food_waste=preprocess_text(profile.get("food_waste", ""))
    if waste: parts.append(f"waste management segregation {waste} recycling compost")
    if food_waste: parts.append(f"food waste leftovers scraps {food_waste} compost kitchen")
    shopping=preprocess_text(profile.get("shopping_habit", profile.get("shopping_frequency", "")))
    if shopping: parts.append(f"shopping purchases consumption {shopping} packaging reuse repair durable")
    if profile.get("shops_in_person") is True: parts.append("shops in person groceries reusable bag")
    return preprocess_text(" ".join(parts))

def _eligible(row, profile):
    condition=str(row["eligibility"])
    commute=preprocess_text(profile.get("commute", profile.get("commute_mode", "")))
    diet=preprocess_text(profile.get("diet", profile.get("diet_pattern", "")))
    water=preprocess_text(profile.get("water_usage", ""))
    food_waste=preprocess_text(profile.get("food_waste", ""))
    shopping=preprocess_text(profile.get("shopping_habit", ""))
    if condition == "public_transport_available" and profile.get("public_transport_available") is False: return False
    if condition == "short_trip_suitable" and profile.get("short_trips_suitable") is False: return False
    if condition == "uses_private_vehicle" and not any(term in commute for term in ("car","petrol","diesel","two wheeler","scooter","motorcycle")): return False
    if condition == "uses_air_conditioner" and profile.get("ac",profile.get("ac_usage")) in (None,"Rarely","Never"): return False
    if condition == "has_plants" and profile.get("has_plants") is False: return False
    if condition == "planning_fixture_replacement" and profile.get("planning_fixture_replacement") is False: return False
    if condition == "has_non_plant_based_meals" and diet in {"vegan","vegetarian"}: return False
    if condition == "food_waste_reported" and food_waste in {"none","rarely","low"}: return False
    if condition == "composting_possible" and profile.get("composting_possible") is False: return False
    if condition == "segregation_service_available" and profile.get("segregation_service_available") is False: return False
    if condition == "shops_in_person" and profile.get("shops_in_person") is False: return False
    if condition == "refill_access" and profile.get("refill_access") is False: return False
    if condition == "has_e_waste" and profile.get("has_e_waste") is False: return False
    if condition == "buys_durable_goods" and profile.get("buys_durable_goods") is False: return False
    if condition == "frequent_shopping" and shopping not in {"often","frequently","weekly","very often"}: return False
    if condition == "planning_purchase" and profile.get("planning_purchase") is False: return False
    if condition == "has_reusable_items" and profile.get("has_reusable_items") is False: return False
    return True

def _category_relevance(profile):
    """Estimate which profile areas have stronger user-specific needs (0 to 1)."""
    commute=preprocess_text(profile.get("commute",profile.get("commute_mode","")))
    distance=float(profile.get("commute_km",profile.get("commute_km_day",0)) or 0)
    days=int(profile.get("commute_days",profile.get("commute_days_week",0)) or 0)
    if any(x in commute for x in ("petrol","diesel","car","two wheeler","motorcycle")):
        transport=min(1.0, .45 + distance/40 + days/20)
    elif "public transport" in commute or "bus" in commute or "metro" in commute:
        transport=.35 if distance>0 else .15
    elif "walk" in commute or "cycle" in commute: transport=.15
    else: transport=.05
    electricity=float(profile.get("electricity",profile.get("electricity_kwh_month",0)) or 0)
    electricity_score=min(1.0,electricity/400)
    if profile.get("ac",profile.get("ac_usage")) in ("Some days","Most days"): electricity_score=min(1,electricity_score+.12)
    water=preprocess_text(profile.get("water_usage",profile.get("shower_habit","")))
    water_score={"high":.95,"moderate":.55,"medium":.55,"low":.2}.get(water,.3)
    diet=preprocess_text(profile.get("diet",profile.get("diet_pattern","")))
    food_score={"mixed diet":.9,"mixed":.9,"mostly plant based":.65,"vegetarian":.4,"vegan":.3}.get(diet,.45)
    if preprocess_text(profile.get("food_waste",""))=="often": food_score=min(1,food_score+.12)
    segregation=preprocess_text(profile.get("segregation",profile.get("waste_segregation","")))
    waste_score={"not yet":.95,"sometimes":.7,"always":.35}.get(segregation,.4)
    shopping=preprocess_text(profile.get("shopping_habit",profile.get("shopping_frequency","")))
    shopping_score={"very often":.95,"often":.8,"weekly":.75,"monthly":.45,"rarely":.2}.get(shopping,.4)
    return {"Transportation":transport,"Electricity":electricity_score,"Water":water_score,"Food":food_score,"Waste":waste_score,"Shopping":shopping_score}

def _matched_habits(profile, category):
    """Explain the user-provided profile signals used for this action category."""
    details=[]
    if category=="Transportation":
        mode=profile.get("commute",profile.get("commute_mode"))
        distance=profile.get("commute_km",profile.get("commute_km_day",0))
        days=profile.get("commute_days",profile.get("commute_days_week",0))
        if mode: details.append(f"Main commute: {mode}")
        if float(distance or 0)>0 and int(days or 0)>0:
            details.append(f"Commute: {distance:g} km/day on {days} days/week")
        if profile.get("public_transport_available") is True:
            details.append("Public transport is marked practical for you")
    elif category=="Electricity":
        electricity=profile.get("electricity",profile.get("electricity_kwh_month",0))
        if float(electricity or 0)>0: details.append(f"Home electricity: {electricity:g} kWh/month")
        ac=profile.get("ac",profile.get("ac_usage"))
        if ac: details.append(f"Air conditioning: {ac}")
    elif category=="Water":
        value=profile.get("water_usage",profile.get("shower_habit"))
        if value: details.append(f"Reported water use: {value}")
    elif category=="Food":
        diet=profile.get("diet",profile.get("diet_pattern"))
        waste=profile.get("food_waste")
        if diet: details.append(f"Diet pattern: {diet}")
        if waste: details.append(f"Food waste frequency: {waste}")
    elif category=="Waste":
        segregation=profile.get("segregation",profile.get("waste_segregation"))
        waste=profile.get("food_waste")
        if segregation: details.append(f"Waste sorting: {segregation}")
        if waste: details.append(f"Food waste frequency: {waste}")
    elif category=="Shopping":
        frequency=profile.get("shopping_habit",profile.get("shopping_frequency"))
        if frequency: details.append(f"Shopping frequency: {frequency}")
        if profile.get("shops_in_person") is not None:
            details.append("You shop in person" if profile["shops_in_person"] else "You do not usually shop in person")
    return details or [f"General sustainable-lifestyle profile signals for {category.lower()}"]

def recommend(profile, top_n=6, catalogue=None):
    """Return personalized actions, ranked by profile-item TF-IDF cosine similarity.

    Cosine similarity is the principal ranking signal. Small transparent boosts
    use explicit category activity, feasibility, and catalogue impact tier. These
    scores indicate text/profile match, not measured emissions reductions.
    """
    top_n=max(1,min(int(top_n),30))
    frame=(catalogue.copy() if catalogue is not None else load_catalogue())
    if "document" not in frame:
        frame["document"]=frame.apply(lambda row: preprocess_text(" ".join(str(row.get(col,"")) for col in ("category","title","description","match_terms"))),axis=1)
    profile_text=_profile_document(profile)
    if not profile_text:
        profile_text="sustainable lifestyle household daily habits environment"
    eligible=frame[frame.apply(lambda row:_eligible(row,profile),axis=1)].copy()
    if eligible.empty: return []
    # Fit on the action descriptions and this user's current profile query.
    vectorizer=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,stop_words="english")
    matrix=vectorizer.fit_transform([*eligible["document"].tolist(),profile_text])
    similarities=cosine_similarity(matrix[-1],matrix[:-1]).ravel()
    category_relevance=_category_relevance(profile)
    ranked=[]
    for (_,row),similarity in zip(eligible.iterrows(),similarities):
        category=float(category_relevance.get(row["category"],0.0))
        impact=(IMPACT_ORDER.get(str(row["impact_tier"]).lower(),1)-1)/2
        difficulty=(5-int(row["difficulty"]))/4
        budget=float(profile.get("budget",profile.get("monthly_budget_inr",0)) or 0)
        cost_fit=1.0 if row["cost_tier"]=="low" or budget>=2500 else .65 if row["cost_tier"]=="medium" else .3
        score=.62*float(similarity)+.22*category+.08*difficulty+.05*impact+.03*cost_fit
        item={key:row[key] for key in ("action_id","category","title","description","eligibility","impact_tier","cost_tier","difficulty","source_name","source_url")}
        habits=_matched_habits(profile,row["category"])
        reason=f"Matched to your {row['category'].lower()} profile: " + "; ".join(habits) + f". Catalogue text match: {similarity:.0%}; category-fit signal: {category:.0%}."
        if cost_fit>=.95: reason+=" Low-cost or no-cost to try."
        item.update({"similarity":round(float(similarity),4),"category_fit":round(category,4),"matched_habits":habits,"relevance_score":round(score,4),"reason":reason,"rank_position":0})
        ranked.append(item)
    ranked.sort(key=lambda item:(-item["relevance_score"],-item["similarity"],item["action_id"]))
    for rank,item in enumerate(ranked[:top_n],1): item["rank_position"]=rank
    return ranked[:top_n]
