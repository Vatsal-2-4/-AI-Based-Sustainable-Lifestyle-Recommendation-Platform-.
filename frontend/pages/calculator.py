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
    "tomatoes":"Tomatoes","bananas":"Bananas",
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
    # Earlier UI versions stored bananas under "fruit"; migrate that saved input.
    if "fruit" in food and "bananas" not in food:
        food={**food,"bananas":food["fruit"]}
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
    st.markdown("""<section class="calc-hero"><div class="calc-kicker">EVERGREEN · PERSONAL IMPACT</div><h1>Make your everyday<br>impact visible.</h1><p>Adjust a few familiar habits and explore a transparent estimate of your annual footprint. Your results update as you go.</p></section>""",unsafe_allow_html=True)
    profile=st.session_state.get("profile",{})
    prefix=_prepare_input_state(st.session_state.user_id,profile)
    st.markdown("<div class='calc-content'></div>",unsafe_allow_html=True)
    left,right=st.columns([1.05,.95],gap="large")
    with left:
        st.markdown("<div class='calc-section-label'><span>✳</span> Quick estimate</div><p style='margin:.45rem 0 1rem;color:#aebaa6;font-size:.82rem'>Start with monthly fuel and electricity. The estimate updates as you type.</p>",unsafe_allow_html=True)
        st.caption("Use one month's bill and a typical month of fuel. Example: 120 kWh and 8 litres. Saved values are prefilled when available; no commute or diet amounts are guessed.")
        with st.container(border=True):
            st.markdown("**🚗 Transport · monthly fuel for your own vehicle**")
            a,b=st.columns(2)
            with a: petrol=st.number_input("Petrol · litres/month",min_value=0.0,max_value=1000.0,step=1.0,key=prefix+"petrol",help="Example: about 8 litres in a typical month.")
            with b: diesel=st.number_input("Diesel · litres/month",min_value=0.0,max_value=1000.0,step=1.0,key=prefix+"diesel",help="Example: about 12 litres in a typical month.")
            st.markdown("**⚡ Home · electricity from your bill**")
            electricity=st.number_input("Electricity · kWh/month",min_value=0.0,max_value=100000.0,step=10.0,key=prefix+"electricity",help="Use one month's kWh from your bill. Your saved profile value is prefilled when available.")
        st.info("Food, water, and waste values from a previous saved estimate stay included and can be reviewed in the details below. If no saved amounts exist, they are left unreported; none are guessed from your lifestyle profile.")
        with st.expander("Add detail to your estimate · food, water & waste",expanded=False):
            detail_tab,food_tab,waste_tab=st.tabs(["⌂  Water","🥗  Food","♻  Waste"])
            with detail_tab:
                st.caption("Water is reported as a volume only. No locally matched household emissions factor is applied.")
                water=st.number_input("Water · litres/person/day",min_value=0.0,max_value=5000.0,step=10.0,key=prefix+"water",help="Example: divide a household meter estimate by the number of residents.")
            with food_tab:
                st.caption("Approximate food purchased or eaten. Enter kilograms per week; for example, 0.5 kg of rice each week.")
                foods=list(FOOD_INPUTS.items())
                for start in range(0,len(foods),3):
                    cols=st.columns(3)
                    for col,(key,label) in zip(cols,foods[start:start+3]):
                        with col:
                            st.number_input(f"{label} · kg/week",min_value=0.0,max_value=200.0,step=0.1,key=prefix+"food_"+key,help=f"Approximate kilograms of {label.lower()} eaten or bought in a week.")
            with waste_tab:
                st.caption("Track weekly material amounts as a resource indicator. Waste is not added to the emissions total.")
                a,b,c=st.columns(3)
                with a: st.number_input("Food waste · kg/week",0.0,500.0,step=.1,key=prefix+"waste_food scraps")
                with b: st.number_input("Recyclables · kg/week",0.0,500.0,step=.1,key=prefix+"waste_dry recyclables")
                with c: st.number_input("Other waste · kg/week",0.0,500.0,step=.1,key=prefix+"waste_residual waste")
        st.caption("ⓘ Water and waste are shown separately because reliable, locally matched household emission factors are not available for these inputs.")
    # Streamlit renders collapsed expander and tab contents, keeping all widget values available.
    electricity=st.session_state.get(prefix+"electricity",float(profile.get("electricity",0) or 0))
    water=st.session_state.get(prefix+"water",0.0)
    food={key:st.session_state.get(prefix+"food_"+key,0.0) for key in FOOD_INPUTS}
    waste={key:st.session_state.get(prefix+"waste_"+key,0.0) for key in ("food scraps","dry recyclables","residual waste")}
    petrol=st.session_state.get(prefix+"petrol",0.0)
    diesel=st.session_state.get(prefix+"diesel",0.0)
    inputs={"petrol_l_month":petrol,"diesel_l_month":diesel,"electricity_kwh_month":electricity,"water_l_person_day":water,"food_kg_week":food,"waste_kg_week":waste}
    try:
        result=calculate_footprint(inputs)
    except ValueError as exc:
        st.error(f"Please check the activity inputs: {exc}")
        return
    except Exception:
        st.error("The calculator could not load its factor data. Try again or check the local factor files.")
        return
    missing_emissions=[]
    if petrol+diesel<=0: missing_emissions.append("Transport fuel (petrol or diesel litres per month)")
    if electricity<=0: missing_emissions.append("Electricity (kWh per month)")
    if sum(food.values())<=0: missing_emissions.append("Food product quantities (kg per week)")
    missing_indicators=[]
    if water<=0: missing_indicators.append("Water use (litres per person per day)")
    if sum(waste.values())<=0: missing_indicators.append("Waste amounts (kg per week)")
    with right:
        st.markdown(f"<div class='calc-live'><div class='calc-live-label'>Estimated annual footprint</div><div class='calc-live-value'>{result['total_kg_co2e']:,.0f}<span style='font:500 1rem system-ui;color:#e5eddd'> kg CO₂e</span></div><div class='calc-live-note'>{result['total_kg_co2e']/1000:.2f} tonnes/year · updates with your inputs</div></div>",unsafe_allow_html=True)
        st.markdown(f"<div style='height:12px'></div><div class='calc-mini'><div class='calc-mini-label'>ESTIMATE SCOPE</div><div class='calc-mini-value'>Partial · {result['factor_version']}</div></div>",unsafe_allow_html=True)
        if missing_emissions or missing_indicators:
            with st.expander(f"Input check · {len(missing_emissions)+len(missing_indicators)} values unreported",expanded=bool(missing_emissions)):
                if missing_emissions:
                    st.markdown("**Emissions categories with no amount entered**")
                    for item in missing_emissions: st.markdown(f"- {item}")
                if missing_indicators:
                    st.markdown("**Optional resource indicators with no amount entered**")
                    for item in missing_indicators: st.markdown(f"- {item}")
                st.caption("A value of 0 is treated as no reported activity. The result is partial and does not mean the unentered activities have no impact.")
        st.caption("Annualized from monthly fuel/electricity and weekly food. Transport covers direct fuel combustion; electricity uses an India grid average; food factors are global product averages. Water and waste are tracked separately and excluded from CO₂e.")
        st.markdown("<div style='height:14px'></div><div class='calc-section-label'>Where your estimate comes from</div>",unsafe_allow_html=True)
        emissions=pd.DataFrame([{"Category":k,"kg CO₂e/year":v} for k,v in result["category_kg_co2e"].items() if v>0])
        if not emissions.empty:
            fig=px.pie(emissions,names="Category",values="kg CO₂e/year",hole=.68,color_discrete_sequence=["#d6ff4f","#79bd73","#4c8659"])
            fig.update_traces(textposition="outside",textinfo="label+percent",marker=dict(line=dict(color="#1b211b",width=3)),hole=0.67)
            fig.update_layout(showlegend=False,margin=dict(t=12,b=18,l=30,r=30),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(family="DM Sans",color="#e5ebdf"),height=300,annotations=[dict(text="ANNUAL<br>CO₂e",x=.5,y=.5,showarrow=False,font=dict(size=13,color="#c6d0bd"))])
            st.plotly_chart(fig,use_container_width=True)
        else:
            st.warning("Enter your activity amounts to see category emissions.")
        cards=st.columns(3)
        icons={"Transportation":"↗","Electricity":"ϟ","Food":"◌"}
        for col,(category,value) in zip(cards,result["category_kg_co2e"].items()):
            with col:
                share=f"{value/result['total_kg_co2e']:.0%} share" if result["total_kg_co2e"] else "No activity"
                st.markdown(f"<div class='calc-mini'><div class='calc-mini-label'>{icons.get(category,'✳')} &nbsp;{category.upper()}</div><div class='calc-mini-value'>{value:,.0f} kg</div><div class='calc-mini-label'>{share}</div></div>",unsafe_allow_html=True)
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
