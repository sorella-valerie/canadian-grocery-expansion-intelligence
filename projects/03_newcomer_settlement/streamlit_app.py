from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parents[1]

@st.cache_data
def load_data():
    cities = pd.read_csv(ROOT / "01_canada_affordability_opportunity/data/processed/city_profiles.csv")
    wages = pd.read_csv(ROOT / "01_canada_affordability_opportunity/data/processed/occupation_wages.csv")
    facilities = pd.read_csv(ROOT / "02_canadian_healthcare_access/data/processed/facilities.csv")
    health = facilities.groupby("city", as_index=False).size().rename(columns={"size":"health_facilities"})
    health["city_key"] = health.city.str.lower()
    cities["city_key"] = cities.city.str.lower()
    return cities.merge(health[["city_key","health_facilities"]], on="city_key", how="left"), wages

def norm(s, higher=True):
    z=(s-s.min())/(s.max()-s.min()) if s.max()>s.min() else pd.Series(.5,index=s.index)
    return z if higher else 1-z

st.set_page_config(page_title="Newcomer settlement navigator", page_icon=":material/travel_explore:", layout="wide")
cities,wages=load_data()
with st.sidebar:
    st.title("Your priorities")
    occupation=st.selectbox("Occupation",sorted(wages.occupation.unique()))
    household=st.number_input("Household size",1,6,2)
    bedrooms=st.segmented_control("Home",["1 bedroom","2 bedrooms"],default="2 bedrooms")
    priority=st.selectbox("Most important",["Balanced fit","Lower living costs","Higher local wage","Healthcare footprint"])

rent="rent_1br" if bedrooms=="1 bedroom" else "rent_2br"
d=cities.merge(wages[wages.occupation.eq(occupation)],on="city")
d["monthly_food"]=d.monthly_food_per_person*household
d["monthly_core_cost"]=d[rent]+d.monthly_food
d["health_facilities"]=d.health_facilities.fillna(0)
weights={"Balanced fit":(.4,.35,.25),"Lower living costs":(.65,.2,.15),"Higher local wage":(.25,.6,.15),"Healthcare footprint":(.25,.2,.55)}[priority]
d["score"]=(norm(d.monthly_core_cost,False)*weights[0]+norm(d.median_annual_wage)*weights[1]+norm(d.health_facilities)*weights[2])*100
d=d.sort_values("score",ascending=False).reset_index(drop=True); d["rank"]=d.index+1
best=d.iloc[0]; second=d.iloc[1]

st.title("Newcomer settlement navigator")
st.write("Compare wages, rent, groceries, and mapped healthcare facilities across ten cities.")
st.caption("Official source measures are preserved. Household costs and the settlement score are derived scenarios, not official immigration or relocation guidance.")
with st.container(border=True):
    st.subheader(f"Best fit: {best.city}. It combines CAD {best.median_annual_wage:,.0f} local median pay with about CAD {best.monthly_core_cost:,.0f} in monthly rent and groceries.")
    st.caption(f"{second.city} ranks second. The recommendation changes when you change the occupation, household, home, or priority.")

cols=st.columns(4)
cols[0].metric("Derived best fit",best.city,border=True)
cols[1].metric("Official median wage",f"${best.median_annual_wage:,.0f}",border=True)
cols[2].metric("Derived core costs",f"${best.monthly_core_cost:,.0f}/mo",border=True)
cols[3].metric("Official mapped facilities",f"{best.health_facilities:,.0f}",border=True)

st.subheader("What the selected scenario shows")
summary_components=d[["city"]].copy(); summary_components["Cost fit"]=norm(d.monthly_core_cost,False)*100; summary_components["Wage fit"]=norm(d.median_annual_wage)*100; summary_components["Facility footprint"]=norm(d.health_facilities)*100
summary_long=summary_components.melt("city",var_name="Component",value_name="Position")
top_left,top_right=st.columns(2)
with top_left.container(border=True):
    st.markdown("**Wage and household-cost frontier**")
    st.altair_chart(alt.Chart(d).mark_circle(opacity=.85).encode(x=alt.X("monthly_core_cost:Q",title="Monthly core costs",scale=alt.Scale(zero=False)),y=alt.Y("median_annual_wage:Q",title="Official median wage",scale=alt.Scale(zero=False)),size=alt.Size("health_facilities:Q",legend=None,scale=alt.Scale(range=[100,700])),color=alt.condition("datum.rank == 1",alt.value("#C65310"),alt.value("#153A47")),tooltip=["city","score"]),height=280)
    st.caption(f"{best.city} pairs a ${best.median_annual_wage:,.0f} wage with ${best.monthly_core_cost:,.0f} in monthly core costs.")
with top_right.container(border=True):
    st.markdown("**Settlement fit ranking**")
    st.altair_chart(alt.Chart(d).mark_bar(cornerRadiusEnd=5).encode(x=alt.X("score:Q",title="Scenario score",scale=alt.Scale(domain=[0,100])),y=alt.Y("city:N",sort="-x",title=None),color=alt.condition("datum.rank == 1",alt.value("#C65310"),alt.value("#153A47")),tooltip=["city","score"]),height=280)
    st.caption(f"{best.city} scores {best.score:.0f}. {second.city} is next at {second.score:.0f}.")
bottom_left,bottom_right=st.columns(2)
with bottom_left.container(border=True):
    st.markdown("**Strength and compromise matrix**")
    st.altair_chart(alt.Chart(summary_long).mark_rect(cornerRadius=3).encode(x=alt.X("Component:N",title=None),y=alt.Y("city:N",sort=d.city.tolist(),title=None),color=alt.Color("Position:Q",scale=alt.Scale(range=["#FBF3EF","#153A47"])),tooltip=["city","Component","Position"]),height=285)
    st.caption("Darker cells indicate a higher position within the ten selected cities. Values are normalized scenario components.")
with bottom_right.container(border=True):
    st.markdown("**Geographic settlement pattern**")
    st.map(d.rename(columns={"latitude":"lat","longitude":"lon"}),latitude="lat",longitude="lon",size="score",color="#C65310",height=285)
    st.caption(f"Marker size shows the scenario score. {best.city} has the largest marker at {best.score:.0f}.")

frontier, profile, map_tab, evidence = st.tabs(["Settlement frontier", "City scorecards", "Access map", "Official evidence"])
with frontier:
    st.subheader("Wage and cost frontier")
    st.caption("Upper left means higher official wage and lower derived monthly core cost. Bubble size shows mapped facility records.")
    scatter=alt.Chart(d).mark_circle(opacity=.85).encode(
        x=alt.X("monthly_core_cost:Q",title="Derived monthly rent and groceries ($)",scale=alt.Scale(zero=False)),
        y=alt.Y("median_annual_wage:Q",title="Official local median wage ($)",scale=alt.Scale(zero=False)),
        size=alt.Size("health_facilities:Q",title="Mapped facilities",scale=alt.Scale(range=[120,900])),
        color=alt.condition("datum.rank == 1",alt.value("#C65310"),alt.value("#153A47")),
        tooltip=["city",alt.Tooltip("median_annual_wage",format="$,.0f"),alt.Tooltip("monthly_core_cost",format="$,.0f"),"health_facilities",alt.Tooltip("score",format=".0f")])
    st.altair_chart(scatter)
    st.caption(f"{best.city} leads for the active priority mix. {second.city} is the closest alternative.")

with profile:
    components=d[["city"]].copy(); components["Living-cost fit"]=norm(d.monthly_core_cost,False)*100; components["Wage fit"]=norm(d.median_annual_wage)*100; components["Healthcare footprint"]=norm(d.health_facilities)*100
    long=components.melt("city",var_name="Component",value_name="Normalized score")
    heat=alt.Chart(long).mark_rect(cornerRadius=3).encode(x=alt.X("Component:N",title=None),y=alt.Y("city:N",sort=d.city.tolist(),title=None),color=alt.Color("Normalized score:Q",scale=alt.Scale(range=["#FBF3EF","#153A47"])),tooltip=["city","Component",alt.Tooltip("Normalized score",format=".0f")])
    st.altair_chart(heat)
    strengths={"living cost":norm(d.monthly_core_cost,False),"local wage":norm(d.median_annual_wage),"healthcare footprint":norm(d.health_facilities)}
    lead=d.index[d.city.eq(best.city)][0]; vals={k:v.loc[lead] for k,v in strengths.items()}
    st.info(f"{best.city}: {max(vals,key=vals.get)} scores {max(vals.values())*100:.0f}. {min(vals,key=vals.get)} scores {min(vals.values())*100:.0f}.",icon=":material/insights:")

with map_tab:
    st.map(d.rename(columns={"latitude":"lat","longitude":"lon"}),latitude="lat",longitude="lon",size="score",color="#C65310",height=520)
    st.caption("Marker size is the derived scenario score. It is not a government settlement rating.")

with evidence:
    show=d[["rank","city","median_annual_wage",rent,"monthly_food","health_facilities","score"]].copy()
    show.columns=["Scenario rank","City","Official median wage","Official rent","Derived groceries","Official mapped facilities","Scenario score"]
    st.dataframe(show,hide_index=True,key="settlement_evidence",column_config={"Official median wage":st.column_config.NumberColumn(format="$%.0f"),"Official rent":st.column_config.NumberColumn(format="$%.0f"),"Derived groceries":st.column_config.NumberColumn(format="$%.0f"),"Scenario score":st.column_config.ProgressColumn(min_value=0,max_value=100,format="%.0f")})

with st.expander("Sources and method",icon=":material/database:"):
    st.markdown("Rent: Statistics Canada 34-10-0133-01. Food: Statistics Canada 18-10-0245-02. Wages: Government of Canada Job Bank 2025. Facilities: Statistics Canada ODHF. The score is a transparent portfolio scenario, not an official indicator.")

