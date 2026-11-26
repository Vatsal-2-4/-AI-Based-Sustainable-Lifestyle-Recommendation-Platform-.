import streamlit as st
from database.repository import save_lifestyle_response, update_user

def _go_to_calculator():
    st.session_state.page="Carbon footprint"
    st.session_state.nav="Carbon footprint"

def render():
    st.title("Lifestyle questionnaire")
    st.caption("A few details help us calculate an estimate and tailor suggestions.")
    profile_complete=st.session_state.get("questionnaire_saved",False)
    st.progress(0.25,text="Step 1 of 4 · Lifestyle profile")
    if profile_complete: st.caption("Step 1 complete. Your profile stays saved when you continue.")
    p=st.session_state.profile
    widget_prefix=f"profile_{st.session_state.user_id}_"
    with st.form("lifestyle_form"):
        st.subheader("🚲 Transport")
        a,b,c=st.columns(3)
        with a: commute=st.selectbox("Main commute mode",["Petrol / diesel car","Public transport","Two-wheeler","Walk or cycle","Work from home"],index=["Petrol / diesel car","Public transport","Two-wheeler","Walk or cycle","Work from home"].index(p['commute']),key=widget_prefix+"commute")
        with b: commute_km=st.number_input("Commute distance (km/day)",0,250,p['commute_km'],key=widget_prefix+"commute_km",help="Enter your typical total commute distance for a day, from 0 to 250 km.")
        with c: days=st.slider("Commute days per week",0,7,p['commute_days'],key=widget_prefix+"commute_days",help="Choose a whole number from 0 to 7.")
        st.subheader("🥗 Food and home")
        a,b,c=st.columns(3)
        with a: diet=st.selectbox("Diet pattern",["Mixed diet","Mostly plant-based","Vegetarian","Vegan"],index=["Mixed diet","Mostly plant-based","Vegetarian","Vegan"].index(p['diet']),key=widget_prefix+"diet")
        with b: housing=st.selectbox("Housing type",["Owned house","Rented apartment","Owned apartment"],index=["Owned house","Rented apartment","Owned apartment"].index(p['housing']),key=widget_prefix+"housing")
        with c: budget=st.number_input("Monthly change budget (₹)",0,100000,p['budget'],step=500,key=widget_prefix+"budget",help="Enter a non-negative amount up to ₹100,000 per month.")
        st.subheader("🏡 Energy and waste")
        a,b,c=st.columns(3)
        with a: electricity=st.number_input("Monthly electricity (kWh)",0,5000,p['electricity'],key=widget_prefix+"electricity",help="Copy the kWh from your bill. Enter a value from 0 to 5,000.")
        with b: ac=st.selectbox("Air conditioning use",["Rarely","Some days","Most days"],index=["Rarely","Some days","Most days"].index(p['ac']),key=widget_prefix+"ac")
        with c: segregation=st.selectbox("Waste segregation",["Always","Sometimes","Not yet"],index=["Always","Sometimes","Not yet"].index(p['segregation']),key=widget_prefix+"segregation")
        st.subheader("💧 Water, food waste, and shopping")
        a,b,c=st.columns(3)
        with a: water_usage=st.selectbox("Household water use",["Low","Moderate","High"],index=["Low","Moderate","High"].index(p.get('water_usage','Moderate')),key=widget_prefix+"water_usage")
        with b: food_waste=st.selectbox("How often is food wasted?",["Rarely","Sometimes","Often"],index=["Rarely","Sometimes","Often"].index(p.get('food_waste','Sometimes')),key=widget_prefix+"food_waste")
        with c: shopping_habit=st.selectbox("How often do you buy non-food items?",["Rarely","Monthly","Weekly","Very often"],index=["Rarely","Monthly","Weekly","Very often"].index(p.get('shopping_habit','Monthly')),key=widget_prefix+"shopping_habit")
        a,b,c=st.columns(3)
        with a: public_transport_available=st.checkbox("Public transport is practical for my commute",value=p.get('public_transport_available',True),key=widget_prefix+"public_transport")
        with b: shops_in_person=st.checkbox("I shop in person at least sometimes",value=p.get('shops_in_person',True),key=widget_prefix+"shops_in_person")
        with c: composting_possible=st.checkbox("I can compost or access composting",value=p.get('composting_possible',False),key=widget_prefix+"composting")
        st.subheader("📍 Location")
        name=st.text_input("Name",p['name'],key=widget_prefix+"name"); city=st.text_input("City",p['city'],key=widget_prefix+"city")
        saved=st.form_submit_button("Save lifestyle profile →",type="primary",use_container_width=True)
    if saved:
        validation_errors=[]
        if not name.strip(): validation_errors.append("Enter your name (1–120 characters).")
        elif len(name.strip())>120: validation_errors.append("Your name must be 120 characters or fewer.")
        if not city.strip(): validation_errors.append("Enter your city (1–120 characters).")
        elif len(city.strip())>120: validation_errors.append("Your city must be 120 characters or fewer.")
        if validation_errors:
            for message in validation_errors: st.error(message)
        else:
            st.session_state.profile.update(name=name.strip(),city=city.strip(),commute=commute,commute_km=commute_km,commute_days=days,diet=diet,housing=housing,budget=budget,electricity=electricity,ac=ac,segregation=segregation,water_usage=water_usage,food_waste=food_waste,shopping_habit=shopping_habit,public_transport_available=public_transport_available,shops_in_person=shops_in_person,composting_possible=composting_possible)
            try:
                update_user(st.session_state.user_id,display_name=name.strip())
                response_id = save_lifestyle_response(st.session_state.user_id, {
                    "city":city.strip(), "commute_mode":commute, "commute_km_day":commute_km,
                    "commute_days_week":days, "diet_pattern":diet, "housing_type":housing,
                    "monthly_budget_inr":budget, "electricity_kwh_month":electricity,
                    "ac_usage":ac, "waste_segregation":segregation,
                    "preferences":{"water_usage":water_usage,"food_waste":food_waste,"shopping_habit":shopping_habit,"public_transport_available":public_transport_available,"shops_in_person":shops_in_person,"composting_possible":composting_possible},
                })
                st.session_state.latest_response_id = response_id
                st.session_state.questionnaire_saved = True
                st.session_state.db_profile_loaded=True
                st.session_state[f"calc_{st.session_state.user_id}_electricity"]=electricity
                st.success("Lifestyle profile saved. Your monthly electricity value will be prefilled in the calculator; other activity amounts are not inferred.")
            except ValueError as exc:
                st.error(str(exc))
            except Exception:
                st.error("We could not save your profile right now. Your answers are still on this page; try saving again.")
    if st.session_state.get("questionnaire_saved",False):
        st.button("Continue to carbon footprint →",type="primary",on_click=_go_to_calculator)
