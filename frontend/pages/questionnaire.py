import streamlit as st
from database.repository import save_lifestyle_response, create_footprint_record

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
        st.subheader("📍 Location")
        name=st.text_input("Name",p['name']); city=st.text_input("City",p['city'])
        saved=st.form_submit_button("Save lifestyle profile →",type="primary",use_container_width=True)
    if saved:
        st.session_state.profile.update(name=name,city=city,commute=commute,commute_km=commute_km,commute_days=days,diet=diet,housing=housing,budget=budget,electricity=electricity,ac=ac,segregation=segregation)
        try:
            response_id = save_lifestyle_response(st.session_state.user_id, {
                "city":city, "commute_mode":commute, "commute_km_day":commute_km,
                "commute_days_week":days, "diet_pattern":diet, "housing_type":housing,
                "monthly_budget_inr":budget, "electricity_kwh_month":electricity,
                "ac_usage":ac, "waste_segregation":segregation,
            })
            st.session_state.latest_response_id = response_id
            diet_tonnes={"Mixed diet":.9,"Mostly plant-based":.72,"Vegetarian":.62,"Vegan":.5}[diet]
            breakdown_tonnes={
                "Transport":round(commute_km*days*52*.006,2),
                "Home energy":round(electricity*12*.005,2),
                "Food":diet_tonnes, "Shopping & waste":.6, "Flights":.18,
            }
            record_id=create_footprint_record(st.session_state.user_id, sum(breakdown_tonnes.values())*1000,
                {key:value*1000 for key,value in breakdown_tonnes.items()}, response_id=response_id)
            st.session_state.latest_footprint_record_id=record_id
            st.success("Lifestyle response and sample footprint saved to SQLite.")
        except Exception as exc:
            st.error(f"Could not save the questionnaire to the database: {exc}")
