import pandas as pd
import plotly.express as px
import streamlit as st
from backend.services.footprint_service import calculate_footprint, source_summary
from database.repository import create_footprint_record, get_footprint_records

FOOD_INPUTS={
    "beef":"Beef (beef herd)","lamb":"Lamb and mutton","pork":"Pork",
    "poultry":"Poultry","prawns":"Farmed prawns","eggs":"Eggs",
    "milk":"Milk","cheese":"Cheese","rice":"Rice","wheat":"Wheat and rye",
    "pulses":"Pulses","tofu":"Tofu","vegetables":"Other vegetables",
    "tomatoes":"Tomatoes","fruit":"Bananas",
}

def _prepare_input_state(user_id, profile):
    prefix=f"calc_{user_id}_"
    loaded_key=f"calculator_inputs_loaded_{user_id}"
    if st.session_state.get(loaded_key):
        return prefix
    records=get_footprint_records(user_id,limit=1)
    snapshot=records[0].get("input_snapshot",{}) if records else {}
    transport=snapshot.get("transport",{})
    food=snapshot.get("food_kg_week",{})
    waste=snapshot.get("waste_kg_week",{})
    defaults={"petrol":transport.get("petrol_l_month",0.0),"diesel":transport.get("diesel_l_month",0.0),
              "electricity":snapshot.get("electricity_kwh_month",float(profile.get("electricity",0) or 0) if st.session_state.get("questionnaire_saved",False) else 0.0),
              "water":snapshot.get("water_l_person_day",0.0)}
    for key,value in defaults.items(): st.session_state.setdefault(prefix+key,value)
    for key in FOOD_INPUTS: st.session_state.setdefault(prefix+"food_"+key,food.get(key,0.0))
    for key in ("food scraps","dry recyclables","residual waste"):
        st.session_state.setdefault(prefix+"waste_"+key,waste.get(key,0.0))
    st.session_state[loaded_key]=True
    return prefix

def _go_to_recommendations():
    st.session_state.page="Recommendations"
    st.session_state.nav="Recommendations"

def render():
    st.title("Carbon footprint calculator")
    st.caption("Enter recent activity amounts to estimate an annual footprint from documented factors.")
    st.info("The CO₂e total covers the categories with available factors below. Water and waste are shown as resource indicators and are not added to that total because reliable, locally matched household factors are not available for these inputs.")
    profile=st.session_state.get("profile",{})
    prefix=_prepare_input_state(st.session_state.user_id,profile)
    left,right=st.columns([1,1.15],gap="large")
    with left:
        st.subheader("Activity inputs")
        st.markdown("**🚗 Transportation**")
        st.caption("Use fuel purchased or consumed for your own vehicles. Shared/public transit is not included in this fuel-based calculation.")
        a,b=st.columns(2)
        with a: petrol=st.number_input("Petrol (litres/month)",min_value=0.0,max_value=1000.0,step=1.0,key=prefix+"petrol")
        with b: diesel=st.number_input("Diesel (litres/month)",min_value=0.0,max_value=1000.0,step=1.0,key=prefix+"diesel")
        st.markdown("**⚡ Electricity**")
        st.caption("Prefilled from your saved lifestyle profile when available. Edit this value if your recent bill differs.")
        electricity=st.number_input("Household electricity (kWh/month)",min_value=0.0,max_value=100000.0,step=10.0,key=prefix+"electricity")
        st.markdown("**💧 Water use**")
        water=st.number_input("Water use (litres/person/day)",min_value=0.0,max_value=5000.0,step=10.0,key=prefix+"water",help="Use a metered or household estimate divided by the number of residents.")
        st.markdown("**🥗 Food consumption**")
        st.caption("Enter approximate kilograms purchased or eaten per week. Zero means no amount was entered.")
        food={}
        with st.expander("Enter food quantities by product",expanded=True):
            foods=list(FOOD_INPUTS.items())
            for start in range(0,len(foods),3):
                cols=st.columns(3)
                for col,(key,label) in zip(cols,foods[start:start+3]):
                    with col: food[key]=st.number_input(f"{label} (kg/week)",min_value=0.0,max_value=200.0,step=0.1,key=prefix+"food_"+key)
        st.markdown("**🗑️ Waste generation**")
        waste={}
        a,b,c=st.columns(3)
        with a: waste["food scraps"]=st.number_input("Food waste (kg/week)",0.0,500.0,step=.1,key=prefix+"waste_food scraps")
        with b: waste["dry recyclables"]=st.number_input("Dry recyclables (kg/week)",0.0,500.0,step=.1,key=prefix+"waste_dry recyclables")
        with c: waste["residual waste"]=st.number_input("Other waste (kg/week)",0.0,500.0,step=.1,key=prefix+"waste_residual waste")
    inputs={"petrol_l_month":petrol,"diesel_l_month":diesel,"electricity_kwh_month":electricity,"water_l_person_day":water,"food_kg_week":food,"waste_kg_week":waste}
    try:
        result=calculate_footprint(inputs)
    except ValueError as exc:
        st.error(f"Please check the activity inputs: {exc}")
        return
    except Exception:
        st.error("The calculator could not load its factor data. Try again or check the local factor files.")
        return
    with right:
        st.subheader("Your estimated annual emissions")
        st.metric("Estimated total from included categories",f"{result['total_kg_co2e']:,.0f} kg CO₂e",help="Partial total: transportation combustion CO₂ + grid electricity CO₂ + food life-cycle CO₂e")
        st.caption(f"Partial estimate · {result['total_kg_co2e']/1000:.2f} tonnes CO₂e/year · factor set {result['factor_version']} · Based on the activity values shown at left")
        st.caption("Included: petrol/diesel combustion, grid electricity, and entered food products. Not included as emissions: water and waste; also outside this estimate are public transit, housing fuels, goods, and services.")
        emissions=pd.DataFrame([{"Category":k,"kg CO₂e/year":v} for k,v in result["category_kg_co2e"].items() if v>0])
        if not emissions.empty:
            fig=px.bar(emissions,x="Category",y="kg CO₂e/year",color="Category",color_discrete_sequence=["#20764b","#67a97c","#a8cfad"])
            fig.update_layout(showlegend=False,margin=dict(t=8,b=8,l=0,r=0),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(family="DM Sans",color="#24352a"),height=320)
            st.plotly_chart(fig,use_container_width=True)
        else:
            st.warning("Enter your activity amounts to see category emissions.")
        st.markdown("**Category breakdown**")
        st.dataframe(pd.DataFrame([{"Category":k,"Estimated kg CO₂e/year":v,"Share":f"{v/result['total_kg_co2e']:.1%}" if result["total_kg_co2e"] else "—"} for k,v in result["category_kg_co2e"].items()]),hide_index=True,use_container_width=True)
        if st.button("Save this estimate",type="primary",use_container_width=True):
            try:
                snapshot={"schema_version":1,"transport":{"petrol_l_month":petrol,"diesel_l_month":diesel},"electricity_kwh_month":electricity,"water_l_person_day":water,"food_kg_week":food,"waste_kg_week":waste}
                record_id=create_footprint_record(st.session_state.user_id,result["total_kg_co2e"],result["category_kg_co2e"],response_id=st.session_state.get("latest_response_id"),factor_version=result["factor_version"],input_snapshot=snapshot)
                st.session_state.latest_footprint_record_id=record_id
                st.success("Estimate saved.")
            except ValueError as exc: st.error(str(exc))
            except Exception: st.error("We could not save this estimate. Check your connection to the local database and try again.")
        if st.session_state.get("latest_footprint_record_id"):
            st.button("Continue to recommended actions →",on_click=_go_to_recommendations,use_container_width=True)
    st.divider()
    water_col,waste_col=st.columns(2)
    with water_col:
        st.subheader("Water use indicator")
        st.metric("Annual water use entered",f"{result['water_litres_year']:,.0f} L/person/year")
        st.caption("Reported as a volume only. Water's associated emissions depend on local abstraction, treatment, pumping, and wastewater systems; no CO₂e is included.")
    with waste_col:
        st.subheader("Waste generation indicator")
        annual_waste=pd.DataFrame([{"Waste stream":k.title(),"kg/year":v} for k,v in result["waste_kg_year"].items()])
        st.metric("Total waste entered",f"{sum(result['waste_kg_year'].values()):,.1f} kg/year")
        if annual_waste["kg/year"].sum()>0:
            fig=px.bar(annual_waste,x="Waste stream",y="kg/year",color="Waste stream",color_discrete_sequence=["#278253","#8dbd99","#d7ad68"])
            fig.update_layout(showlegend=False,margin=dict(t=8,b=8,l=0,r=0),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=260)
            st.plotly_chart(fig,use_container_width=True)
        st.caption("Waste mass is tracked separately; emissions vary by material mix, collection, recycling, composting, and disposal site. No generic landfill factor is assumed.")
    with st.expander("Emission factors and sources"):
        factors,food_factors=source_summary()
        st.markdown("**Electricity** — India grid-average CEA factor: 0.727 kg CO₂/kWh for FY 2023–24 (including renewable generation).")
        st.markdown("[Central Electricity Authority CO₂ Baseline Database](https://cea.nic.in/cdm-co2-baseline-database/)")
        st.markdown("**Petrol and diesel** — IPCC default road-transport CO₂ factor multiplied by default net calorific value and density to derive kg CO₂ per litre. This estimates fuel-combustion CO₂ only.")
        st.write(f"Derived factors used: petrol {result['transport_factor_kg_co2_per_litre']['petrol']:.4f} kg CO₂/L; diesel {result['transport_factor_kg_co2_per_litre']['diesel']:.4f} kg CO₂/L.")
        st.markdown("[IPCC 2006 Guidelines, Volume 2, Chapter 3](https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/2_Volume2/V2_3_Ch3_Mobile_Combustion.pdf) · [Volume 2, Chapter 1](https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/2_Volume2/V2_1_Ch1_Introduction.pdf)")
        st.markdown("**Food** — global mean life-cycle kg CO₂e per kg of product from Poore & Nemecek (2018), processed by Our World in Data. These are global benchmarks, not India-specific supply-chain factors.")
        st.markdown("[Our World in Data food emissions dataset](https://ourworldindata.org/grapher/ghg-per-kg-poore?tab=table) · [Original study, Science (2018)](https://doi.org/10.1126/science.aaq0216)")
        factor_table=factors[factors["factor_id"].isin(["ELEC_IN_CEA_2023_24","PETROL_IPCC_EF","PETROL_IPCC_NCV","PETROL_DENSITY","DIESEL_IPCC_EF","DIESEL_IPCC_NCV","DIESEL_DENSITY"])][["factor_id","factor_value","unit","factor_unit","source_year","limitations"]]
        st.dataframe(factor_table.rename(columns={"factor_id":"Factor","factor_value":"Value","factor_unit":"Factor unit","source_year":"Source year","limitations":"Scope note"}),hide_index=True,use_container_width=True)
        st.dataframe(food_factors[["food_label","kg_co2e_per_kg_product","geographic_scope","data_year"]].rename(columns={"food_label":"Food","kg_co2e_per_kg_product":"kg CO₂e/kg","geographic_scope":"Scope","data_year":"Data year"}),hide_index=True,use_container_width=True)
    with st.expander("Assumptions and limitations"):
        st.markdown("""
- Monthly fuel and electricity inputs are multiplied by 12; weekly food and waste inputs by 52; daily water use by 365.
- Transportation includes direct petrol/diesel combustion only. It excludes vehicle manufacture, fuel production, public transit, and non-CO₂ vehicle gases.
- Electricity uses a national grid average, not the user's state-specific or time-of-day electricity mix.
- Food factors are global averages from data reported for 2010 and published in the 2018 meta-analysis. Product source, recipe, and local production can differ substantially.
- Water use and waste mass are shown as physical indicators, not emissions, and are not included in the CO₂e total.
- This is a partial, approximate footprint, not a full life-cycle assessment or a verified emissions inventory. Zero means no amount was entered; it does not mean the activity has no impact.
""")
    history=get_footprint_records(st.session_state.user_id,limit=5)
    if history:
        st.subheader("Saved footprint estimates")
        st.dataframe([{"Saved":row["created_at"],"Total kg CO₂e":round(row["total_kg_co2e"],1),"Factor set":row["factor_version"],"Input details":"Available" if row["input_snapshot"].get("schema_version")==1 else "Unavailable (older estimate)"} for row in history],hide_index=True,use_container_width=True)
