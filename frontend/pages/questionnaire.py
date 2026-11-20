import streamlit as st

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
        st.success("Your demo profile has been saved.")
        if st.button("Open dashboard"): st.session_state.page="Dashboard"; st.rerun()
