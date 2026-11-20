import streamlit as st
import plotly.express as px
import pandas as pd

def render():
    st.title("Carbon footprint")
    st.caption("Estimate your annual lifestyle emissions. Results are illustrative sample data.")
    left,right=st.columns([1,1.2])
    with left:
        st.subheader("Activity inputs")
        km=st.number_input("Car commute (km/week)",0,1500,st.session_state.profile['commute_km']*st.session_state.profile['commute_days'])
        diet=st.selectbox("Diet pattern",["Mixed diet","Mostly plant-based","Vegetarian","Vegan"],index=["Mixed diet","Mostly plant-based","Vegetarian","Vegan"].index(st.session_state.profile['diet']))
        power=st.number_input("Electricity use (kWh/month)",0,3000,st.session_state.profile['electricity'])
        flights=st.number_input("Flights per year",0,30,1)
        calculate=st.button("Calculate estimate",type="primary",use_container_width=True)
    # Demo coefficients only; replace with sourced factors in backend integration.
    diet_factor={"Mixed diet":.9,"Mostly plant-based":.72,"Vegetarian":.62,"Vegan":.5}[diet]
    values={"Transport":round(km*.006,2),"Home energy":round(power*.005,2),"Food":diet_factor,"Shopping & waste":.6,"Flights":round(flights*.18,2)}
    total=sum(values.values())
    with right:
        st.metric("Estimated annual footprint",f"{total:.1f} t CO₂e",help="Sample estimate; not a verified measurement")
        fig=px.pie(names=list(values),values=list(values.values()),hole=.62,color_discrete_sequence=["#20764b","#62a879","#a4cfad","#d5e9d9","#efbd6a"])
        fig.update_layout(margin=dict(t=10,b=10,l=0,r=0),legend_title_text="Category",paper_bgcolor="rgba(0,0,0,0)",font=dict(family="DM Sans",color="#24352a"),height=320)
        st.plotly_chart(fig,use_container_width=True)
    st.subheader("Category estimates")
    st.dataframe(pd.DataFrame([{"Category":k,"Annual estimate (t CO₂e)":v,"Share":f"{v/total*100:.0f}%"} for k,v in values.items()]),hide_index=True,use_container_width=True)
