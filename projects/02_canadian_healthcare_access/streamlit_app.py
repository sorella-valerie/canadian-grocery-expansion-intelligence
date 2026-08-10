from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
PROVINCES = {"All provinces":"ALL","Alberta":"AB","British Columbia":"BC","Manitoba":"MB","New Brunswick":"NB","Newfoundland and Labrador":"NL","Nova Scotia":"NS","Ontario":"ON","Prince Edward Island":"PE","Quebec":"QC","Saskatchewan":"SK","Northwest Territories":"NT","Nunavut":"NU","Yukon":"YT"}
NAME_TO_CODE = {k:v for k,v in PROVINCES.items() if v != "ALL"}

@st.cache_data
def load_data():
    facilities = pd.read_csv(ROOT / "data/processed/facilities.csv")
    population = pd.read_csv(ROOT / "data/processed/FactPopulation.csv", parse_dates=["Date"])
    latest = population.sort_values("Date").groupby("Geography").tail(1)
    latest["province"] = latest.Geography.map(NAME_TO_CODE)
    return facilities, latest[["province","Population","Date"]].dropna()

st.set_page_config(page_title="Canadian healthcare access map", page_icon=":material/local_hospital:", layout="wide")
data, population = load_data()
with st.sidebar:
    st.title("Explore access")
    province_name = st.selectbox("Province or territory", PROVINCES)
    code = PROVINCES[province_name]
    available = sorted(data.loc[data.province.eq(code), "city"].dropna().unique()) if code != "ALL" else []
    city = st.selectbox("Community", ["All communities"] + available, disabled=code == "ALL")
    types = st.multiselect("Facility types", sorted(data.facility_type.dropna().unique()), default=sorted(data.facility_type.dropna().unique()))

view = data[data.facility_type.isin(types)].copy()
if code != "ALL": view = view[view.province.eq(code)]
if city != "All communities" and code != "ALL": view = view[view.city.eq(city)]
mix = view.facility_type.value_counts(); scope = city if city != "All communities" else province_name
prov_summary = data.groupby(["province","facility_type"]).size().unstack(fill_value=0).reset_index().merge(population,on="province",how="left")
prov_summary["Total facilities"] = prov_summary.filter(regex="Hospitals|Clinics|Residential").sum(axis=1)
prov_summary["Facilities per 100,000"] = prov_summary["Total facilities"] / prov_summary.Population * 100000

st.title("Canadian healthcare access map")
st.write("Filter official facility records by province, community, and facility type.")
st.caption("Official facility records from Statistics Canada ODHF and official quarterly population estimates. Counts describe locations, not beds, staffing, capacity, quality, travel time, or wait times.")
with st.container(border=True):
    if len(view):
        st.subheader(f"{scope}: {len(view):,} mapped facilities across {view.city.nunique():,} communities")
        st.caption(f"Official location count. The largest selected category is {mix.index[0].lower()} at {mix.iloc[0]:,} records. Interpret apparent gaps with the ODHF coverage limitations.")
    else:
        st.warning("No official facility records match these filters.", icon=":material/warning:")
        st.stop()

cols = st.columns(4)
cols[0].metric("Official mapped facilities", f"{len(view):,}", border=True)
cols[1].metric("Official hospital records", f"{view.facility_type.eq('Hospitals').sum():,}", border=True)
cols[2].metric("Communities represented", f"{view.city.nunique():,}", border=True)
cols[3].metric("Geocoded share", f"{len(data)/9039:.1%}", border=True)

st.subheader("What the selected records show")
summary_mix=mix.rename_axis("Facility type").reset_index(name="Facilities")
summary_top=view.groupby(["city","province"],as_index=False).size().nlargest(12,"size")
top_left,top_right=st.columns(2)
with top_left.container(border=True):
    st.markdown("**Mapped facility footprint**")
    st.map(view.rename(columns={"latitude":"lat","longitude":"lon"}),latitude="lat",longitude="lon",size=18,color="#C65310",height=280)
    st.caption(f"{len(view):,} geocoded records are visible for {scope}. {view.city.nunique():,} communities appear in the selection.")
with top_right.container(border=True):
    st.markdown("**Facility mix**")
    st.altair_chart(alt.Chart(summary_mix).mark_bar(cornerRadiusEnd=5).encode(x=alt.X("Facilities:Q"),y=alt.Y("Facility type:N",sort="-x",title=None),color=alt.Color("Facility type:N",scale=alt.Scale(range=["#153A47","#C65310","#29747A"]),legend=None),tooltip=["Facility type","Facilities"]),height=280)
    st.caption(f"{mix.index[0]} accounts for {mix.iloc[0]/len(view):.1%} of selected records.")
bottom_left,bottom_right=st.columns(2)
with bottom_left.container(border=True):
    st.markdown("**Facilities per 100,000 residents**")
    st.altair_chart(alt.Chart(prov_summary).mark_bar(cornerRadiusEnd=5).encode(x=alt.X("Facilities per 100,000:Q",title="Derived rate"),y=alt.Y("province:N",sort="-x",title=None),color=alt.value("#153A47"),tooltip=["province",alt.Tooltip("Facilities per 100,000",format=".1f")]),height=280)
    st.caption(f"{prov_summary.loc[prov_summary['Facilities per 100,000'].idxmax(),'province']} has the highest derived rate at {prov_summary['Facilities per 100,000'].max():.1f} records per 100,000.")
with bottom_right.container(border=True):
    st.markdown("**Largest mapped community footprints**")
    st.altair_chart(alt.Chart(summary_top).mark_bar(cornerRadiusEnd=5).encode(x=alt.X("size:Q",title="Mapped facilities"),y=alt.Y("city:N",sort="-x",title=None),color=alt.value("#C65310"),tooltip=["city","province","size"]),height=280)
    st.caption(f"{summary_top.iloc[0].city} has the largest selected footprint with {summary_top.iloc[0]['size']:,} records.")

footprint, benchmark, communities, evidence = st.tabs(["Facility map", "Provincial benchmark", "Community concentration", "Official records"])
with footprint:
    left,right=st.columns([1.45,1])
    with left.container(border=True):
        st.subheader("Where facilities are mapped")
        st.map(view.rename(columns={"latitude":"lat","longitude":"lon"}),latitude="lat",longitude="lon",size=22,color="#C65310",height=560)
    with right.container(border=True):
        st.subheader("Facility mix")
        chart_data=mix.rename_axis("Facility type").reset_index(name="Facilities")
        st.altair_chart(alt.Chart(chart_data).mark_bar(cornerRadiusEnd=5).encode(x=alt.X("Facilities:Q"),y=alt.Y("Facility type:N",sort="-x",title=None),color=alt.Color("Facility type:N",scale=alt.Scale(range=["#153A47","#C65310","#29747A"]),legend=None),tooltip=["Facility type","Facilities"]))
        st.caption("Official counts by ODHF facility classification.")

with benchmark:
    st.subheader("Mapped footprint relative to population")
    st.caption("Derived rate using two official sources. A higher rate does not prove better access or capacity.")
    rate=alt.Chart(prov_summary).mark_bar(cornerRadiusEnd=5).encode(x=alt.X("Facilities per 100,000:Q"),y=alt.Y("province:N",sort="-x",title="Province or territory"),color=alt.value("#153A47"),tooltip=["province",alt.Tooltip("Population",format=","),alt.Tooltip("Total facilities",format=","),alt.Tooltip("Facilities per 100,000",format=".1f")])
    st.altair_chart(rate)
    stacked=prov_summary.melt(id_vars=["province","Population","Date","Total facilities","Facilities per 100,000"],value_vars=[c for c in ["Hospitals","Clinics and ambulatory care","Residential and long-term care"] if c in prov_summary],var_name="Facility type",value_name="Facilities")
    st.altair_chart(alt.Chart(stacked).mark_bar().encode(x=alt.X("Facilities:Q",stack="normalize",axis=alt.Axis(format="%"),title="Share of mapped facilities"),y=alt.Y("province:N",title=None),color=alt.Color("Facility type:N",scale=alt.Scale(range=["#C65310","#153A47","#29747A"])),tooltip=["province","Facility type","Facilities"]))

with communities:
    community=view.groupby(["city","province","facility_type"],as_index=False).size()
    top=community.groupby(["city","province"],as_index=False)["size"].sum().nlargest(20,"size")
    st.altair_chart(alt.Chart(top).mark_bar(cornerRadiusEnd=5).encode(x=alt.X("size:Q",title="Official mapped facilities"),y=alt.Y("city:N",sort="-x",title=None),color=alt.value("#C65310"),tooltip=["city","province","size"]))
    concentration = top["size"].head(5).sum()/max(view.shape[0],1)
    st.metric("Share located in top five communities",f"{concentration:.1%}",help="Derived concentration measure for the active filters.")

with evidence:
    st.dataframe(view[["facility_name","facility_type","city","province","provider"]].rename(columns={"facility_name":"Facility","facility_type":"Official type","city":"Community","province":"Province","provider":"Source provider"}),hide_index=True,key="official_facilities")
    st.download_button("Download filtered official records",view.to_csv(index=False).encode("utf-8"),"odhf_filtered.csv","text/csv",icon=":material/download:")

with st.expander("Definitions, vintage and limitations",icon=":material/database:"):
    st.markdown("Source: [Statistics Canada Open Database of Healthcare Facilities](https://www.statcan.gc.ca/en/lode/databases/odhf). ODHF is a harmonized listing assembled from public providers. The 7,525 displayed records are the geocoded subset of 9,039 source rows. Population is the latest available quarterly provincial estimate in the prepared official extract. Facility-per-population rates are derived here and are not official access indicators.")

