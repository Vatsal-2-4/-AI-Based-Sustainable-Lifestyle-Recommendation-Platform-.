import streamlit as st
from database.repository import save_lifestyle_response

def render():
    st.title("Lifestyle questionnaire")
    st.caption("A few details help us calculate an estimate and tailor suggestions.")
    st.progress(1.0,text="Lifestyle profile · Complete the form and save")
    p=st.session_state.profile
    with st.form("lifestyle_form"):
        st.subheader("🚲 Transport")
        a,b,c=st.columns(3)
        with a: commute=st.selectbox("Main commute mode",["Petrol / diesel car","Public transport","Two-wheeler","Walk or cycle","Work from home"],index=["Petrol / diesel car","Public transport","Two-wheeler","Walk or cycle","Work from home"].index(p['commute']))
        with b: commute_km=st.number_input("Commute distance (km/day)",0,250,p['commute_km'])
        with c: days=st.slider("Commute days per week",0,7,p['commute_days'])
        st.subheader("🥗 Food and home")
        a,b,c=st.columns(3)
        with a: diet=st.selectbox("Diet pattern",["Mixed diet","Mostly plant-based","Vegetarian","Vegan"],index=["Mixed diet","Mostly plant-based","Vegetarian","Vegan"].index(p['diet']))
        with b: housing=st.selectbox("Housing type",["Owned house","Rented apartment","Owned apartment"],index=["Owned house","Rented apartment","Owned apartment"].index(p['housing']))
        with c: budget=st.number_input("Monthly change budget (₹)",0,100000,p['budget'],step=500)
        st.subheader("🏡 Energy and waste")
        a,b,c=st.columns(3)
        with a: electricity=st.number_input("Monthly electricity (kWh)",0,5000,p['electricity'])
        with b: ac=st.selectbox("Air conditioning use",["Rarely","Some days","Most days"],index=["Rarely","Some days","Most days"].index(p['ac']))
        with c: segregation=st.selectbox("Waste segregation",["Always","Sometimes","Not yet"],index=["Always","Sometimes","Not yet"].index(p['segregation']))
        st.subheader("💧 Water, food waste, and shopping")
        a,b,c=st.columns(3)
        with a: water_usage=st.selectbox("Household water use",["Low","Moderate","High"],index=["Low","Moderate","High"].index(p.get('water_usage','Moderate')))
        with b: food_waste=st.selectbox("How often is food wasted?",["Rarely","Sometimes","Often"],index=["Rarely","Sometimes","Often"].index(p.get('food_waste','Sometimes')))
        with c: shopping_habit=st.selectbox("How often do you buy non-food items?",["Rarely","Monthly","Weekly","Very often"],index=["Rarely","Monthly","Weekly","Very often"].index(p.get('shopping_habit','Monthly')))
        a,b,c=st.columns(3)
        with a: public_transport_available=st.checkbox("Public transport is practical for my commute",value=p.get('public_transport_available',True))
        with b: shops_in_person=st.checkbox("I shop in person at least sometimes",value=p.get('shops_in_person',True))
        with c: composting_possible=st.checkbox("I can compost or access composting",value=p.get('composting_possible',False))
        st.subheader("📍 Location")
        name=st.text_input("Name",p['name']); city=st.text_input("City",p['city'])
        saved=st.form_submit_button("Save lifestyle profile →",type="primary",use_container_width=True)
    if saved:
        st.session_state.profile.update(name=name,city=city,commute=commute,commute_km=commute_km,commute_days=days,diet=diet,housing=housing,budget=budget,electricity=electricity,ac=ac,segregation=segregation,water_usage=water_usage,food_waste=food_waste,shopping_habit=shopping_habit,public_transport_available=public_transport_available,shops_in_person=shops_in_person,composting_possible=composting_possible)
        try:
            response_id = save_lifestyle_response(st.session_state.user_id, {
                "city":city, "commute_mode":commute, "commute_km_day":commute_km,
                "commute_days_week":days, "diet_pattern":diet, "housing_type":housing,
                "monthly_budget_inr":budget, "electricity_kwh_month":electricity,
                "ac_usage":ac, "waste_segregation":segregation,
                "preferences":{"water_usage":water_usage,"food_waste":food_waste,"shopping_habit":shopping_habit,"public_transport_available":public_transport_available,"shops_in_person":shops_in_person,"composting_possible":composting_possible},
            })
            st.session_state.latest_response_id = response_id
            st.session_state.questionnaire_saved = True
            st.success("Lifestyle response saved to SQLite. Open Carbon footprint to calculate using documented factors.")
        except Exception as exc:
            st.error(f"Could not save the questionnaire to the database: {exc}")
