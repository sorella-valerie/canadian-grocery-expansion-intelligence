from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from models import affordability_label, estimate_take_home


ROOT = Path(__file__).parent


@st.cache_data
def load_data():
    cities = pd.read_csv(ROOT / "data" / "processed" / "city_profiles.csv")
    wages = pd.read_csv(ROOT / "data" / "processed" / "occupation_wages.csv")
    return cities, wages


def normalize(series, higher=True):
    spread = series.max() - series.min()
    value = (series - series.min()) / spread if spread else pd.Series(.5, index=series.index)
    return value if higher else 1 - value


st.set_page_config(page_title="Canada affordability explorer", page_icon=":material/location_city:", layout="wide")
cities, wages = load_data()

with st.sidebar:
    st.title("Your move")
    st.caption("Change the inputs, then compare the result across ten Canadian cities.")
    with st.form("scenario"):
        occupation = st.selectbox("Occupation", sorted(wages["occupation"].unique()))
        salary_mode = st.segmented_control("Income basis", ["Local median wage", "My salary"], default="Local median wage")
        salary = st.number_input("Expected annual salary", min_value=25000, max_value=250000, value=55000, step=1000,
                                 disabled=salary_mode == "Local median wage")
        household = st.number_input("Household size", 1, 6, 1)
        bedrooms = st.segmented_control("Home", ["1 bedroom", "2 bedrooms"], default="1 bedroom")
        transport = st.segmented_control("Transportation", ["Transit", "Car"], default="Transit")
        selected_city = st.selectbox("City to inspect", cities["city"].tolist(), index=5)
        submitted = st.form_submit_button("Compare cities", type="primary", icon=":material/analytics:")

st.title("Canada affordability & opportunity explorer")
st.write("Compare wages, rent, groceries, transportation, and monthly money left across ten cities.")
st.caption("Planning model using 2025 Statistics Canada rents and food prices, 2025 Job Bank wages, and 2026 tax parameters.")

rent_col = "rent_1br" if bedrooms == "1 bedroom" else "rent_2br"
comparison = cities.merge(wages[wages["occupation"] == occupation], on="city", how="left")
comparison["gross_income"] = comparison["median_annual_wage"] if salary_mode == "Local median wage" else salary
comparison["take_home_monthly"] = comparison.apply(lambda r: estimate_take_home(r["gross_income"], r["province_code"]) / 12, axis=1)
comparison["food"] = comparison["monthly_food_per_person"] * household
comparison["transport"] = 165 if transport == "Transit" else 850
comparison["remaining"] = comparison["take_home_monthly"] - comparison[rent_col] - comparison["food"] - comparison["transport"]
comparison["rent_share"] = comparison[rent_col] / comparison["take_home_monthly"]
comparison["score"] = (normalize(comparison["remaining"]) * .55 + normalize(comparison["rent_share"], False) * .30 +
                       normalize(comparison["median_annual_wage"]) * .15) * 100
comparison["status"] = comparison.apply(lambda r: affordability_label(r["rent_share"], r["remaining"]), axis=1)
comparison = comparison.sort_values("score", ascending=False).reset_index(drop=True)
comparison["rank"] = comparison.index + 1

chosen = comparison[comparison["city"] == selected_city].iloc[0]
best = comparison.iloc[0]
gap = best["remaining"] - chosen["remaining"]

if selected_city == best["city"]:
    decision = f"{selected_city} ranks first. Your model leaves about ${chosen['remaining']:,.0f} after rent, groceries and {transport.lower()} each month."
else:
    biggest = "housing" if chosen[rent_col] / (chosen[rent_col] + chosen["food"] + chosen["transport"]) > .5 else "basic living costs"
    decision = (f"{selected_city} ranks #{int(chosen['rank'])}. {best['city']} leaves about ${gap:,.0f} more each month. "
                f"The main pressure in {selected_city} is {biggest}, with rent using {chosen['rent_share']:.0%} of take-home pay.")

with st.container(border=True):
    st.subheader(f"Decision: {decision}")
    st.caption(f"Derived planning result: {chosen['status']}. Scenario score {chosen['score']:.0f}/100. The source measures are official; the recommendation and score are not official indicators.")

metric_cols = st.columns(4)
metric_cols[0].metric("Official median wage", f"${chosen['median_annual_wage']:,.0f}", border=True)
metric_cols[1].metric("Official monthly rent", f"${chosen[rent_col]:,.0f}", border=True)
metric_cols[2].metric("Derived take-home", f"${chosen['take_home_monthly']:,.0f}", border=True)
metric_cols[3].metric("Derived money left", f"${chosen['remaining']:,.0f}", chosen["status"], border=True)

st.subheader("What the selected data shows")
summary_budget = pd.DataFrame({"Category":["Rent","Groceries",transport,"Money left"],"Amount":[chosen[rent_col],chosen["food"],chosen["transport"],max(chosen["remaining"],0)]})
top_left, top_right = st.columns(2)
with top_left.container(border=True):
    st.markdown("**Monthly budget composition**")
    st.altair_chart(alt.Chart(summary_budget).mark_bar(cornerRadiusEnd=5).encode(x=alt.X("Amount:Q",title="Monthly amount ($)"),y=alt.Y("Category:N",sort=None,title=None),color=alt.condition("datum.Category == 'Money left'",alt.value("#29747A"),alt.value("#C65310")),tooltip=["Category",alt.Tooltip("Amount",format="$,.0f")]),height=260)
    st.caption(f"Rent is {chosen[rent_col]/chosen['take_home_monthly']:.1%} of estimated take-home. Core costs leave ${chosen['remaining']:,.0f} per month.")
with top_right.container(border=True):
    st.markdown("**City score ranking**")
    st.altair_chart(alt.Chart(comparison).mark_bar(cornerRadiusEnd=5).encode(x=alt.X("score:Q",title="Scenario score",scale=alt.Scale(domain=[0,100])),y=alt.Y("city:N",sort="-x",title=None),color=alt.condition(f"datum.city == '{selected_city}'",alt.value("#C65310"),alt.value("#153A47")),tooltip=["city",alt.Tooltip("score",format=".0f")]),height=260)
    st.caption(f"{selected_city} ranks {int(chosen['rank'])} of {len(comparison)}. {best.city} leads by {best.score-chosen.score:.0f} points.")
bottom_left, bottom_right = st.columns(2)
with bottom_left.container(border=True):
    st.markdown("**Wage versus rent burden**")
    st.altair_chart(alt.Chart(comparison).mark_circle(size=180).encode(x=alt.X("rent_share:Q",axis=alt.Axis(format="%"),title="Rent share"),y=alt.Y("median_annual_wage:Q",title="Official median wage",scale=alt.Scale(zero=False)),color=alt.condition(f"datum.city == '{selected_city}'",alt.value("#C65310"),alt.value("#153A47")),tooltip=["city",alt.Tooltip("rent_share",format=".1%"),alt.Tooltip("median_annual_wage",format="$,.0f")]),height=270)
    st.caption(f"{selected_city}'s wage is ${chosen.median_annual_wage:,.0f}. Its rent share is {chosen.rent_share:.1%} versus a {comparison.rent_share.median():.1%} city median.")
with bottom_right.container(border=True):
    st.markdown("**City locations and score size**")
    st.map(comparison.rename(columns={"latitude":"lat","longitude":"lon"}),latitude="lat",longitude="lon",size="score",color="#C65310",height=270)
    st.caption(f"The largest marker is {best.city} at {best.score:.0f}. Marker size is the derived score.")

overview, tradeoffs, sensitivity, evidence = st.tabs(["Decision overview", "Market trade-offs", "Salary sensitivity", "Official evidence"])
with overview:
    left, right = st.columns([1.2, 1])
    with left.container(border=True):
        st.subheader("Monthly cash flow")
        budget = pd.DataFrame({"Amount": [chosen["take_home_monthly"], -chosen[rent_col], -chosen["food"], -chosen["transport"], chosen["remaining"]],
                               "Step": ["Take-home pay", "Rent", "Groceries", transport, "Money left"],
                               "Type": ["Income", "Cost", "Cost", "Cost", "Balance"]})
        chart = alt.Chart(budget).mark_bar(cornerRadiusEnd=5).encode(
            x=alt.X("Amount:Q", title="Monthly amount ($)"), y=alt.Y("Step:N", sort=None, title=None),
            color=alt.Color("Type:N", scale=alt.Scale(domain=["Income", "Cost", "Balance"], range=["#153A47", "#C65310", "#29747A"]), legend=None),
            tooltip=["Step", alt.Tooltip("Amount", format="$,.0f")])
        st.altair_chart(chart)
    with right.container(border=True):
        st.subheader("Budget thresholds")
        st.metric("Rent burden", f"{chosen['rent_share']:.1%}", "Above 35%" if chosen["rent_share"] >= .35 else "Below 35%", delta_color="inverse")
        st.metric("Core-cost share", f"{(chosen[rent_col]+chosen['food']+chosen['transport'])/chosen['take_home_monthly']:.1%}")
        st.metric("Advantage of top city", f"${gap:,.0f}/mo" if gap > 0 else "$0/mo")
        st.caption("Thresholds and cash-flow outputs are derived planning calculations.")

with tradeoffs:
    with st.container(border=True):
        st.subheader("Income versus housing burden")
        scatter = alt.Chart(comparison).mark_circle(size=260).encode(
            x=alt.X("rent_share:Q", title="Rent share of estimated take-home", axis=alt.Axis(format="%")),
            y=alt.Y("median_annual_wage:Q", title="Official local median wage ($)", scale=alt.Scale(zero=False)),
            color=alt.condition(f"datum.city == '{selected_city}'", alt.value("#C65310"), alt.value("#153A47")),
            tooltip=["city", alt.Tooltip("median_annual_wage", format="$,.0f"), alt.Tooltip("rent_share", format=".1%"), alt.Tooltip("remaining", format="$,.0f")])
        st.altair_chart(scatter)
    st.map(comparison.rename(columns={"latitude":"lat", "longitude":"lon"}), latitude="lat", longitude="lon", size="score", color="#C65310", height=420)

with sensitivity:
    salaries = pd.Series(range(35000, 151000, 5000), name="Salary")
    curve = pd.DataFrame({"Salary": salaries})
    curve["Monthly money left"] = curve.Salary.apply(lambda x: estimate_take_home(x, chosen["province_code"])/12 - chosen[rent_col] - chosen["food"] - chosen["transport"])
    zero = alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(strokeDash=[5,5], color="#A9470E").encode(y="y:Q")
    line = alt.Chart(curve).mark_line(point=True, color="#153A47").encode(x=alt.X("Salary:Q", title="Gross annual salary ($)"), y=alt.Y("Monthly money left:Q", title="Monthly money left ($)"), tooltip=[alt.Tooltip("Salary", format="$,.0f"), alt.Tooltip("Monthly money left", format="$,.0f")])
    st.altair_chart(line + zero)
    st.caption(f"This derived curve holds {selected_city} rent, household size, basket, and {transport.lower()} assumption constant.")

with evidence:
    table = comparison[["rank", "city", "median_annual_wage", rent_col, "monthly_food_per_person", "take_home_monthly", "remaining", "rent_share", "score"]].copy()
    table.columns = ["Scenario rank", "City", "Official median wage", "Official rent", "Derived monthly basket per person", "Derived take-home", "Derived money left", "Derived rent share", "Scenario score"]
    st.dataframe(table, hide_index=True, key="affordability_evidence", column_config={
        "Official median wage": st.column_config.NumberColumn(format="$%.0f"), "Official rent": st.column_config.NumberColumn(format="$%.0f"),
        "Derived monthly basket per person": st.column_config.NumberColumn(format="$%.2f"), "Derived take-home": st.column_config.NumberColumn(format="$%.0f"),
        "Derived money left": st.column_config.NumberColumn(format="$%.0f"), "Derived rent share": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
        "Scenario score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f")})

with st.expander("Method and sources", icon=":material/database:"):
    st.markdown("""
    - Rent: Statistics Canada table 34-10-0133-01, 2025 average rents for row and apartment structures with three or more units.
    - Wages and outlook foundation: Government of Canada Job Bank 2025 wage and 2025 to 2027 outlook open data.
    - Groceries: Statistics Canada table 18-10-0245-02, latest provincial prices applied to a fixed representative basket.
    - Take-home pay: planning estimate using 2026 federal and provincial brackets, CPP and EI parameters. Credits and personal deductions are not modelled.
    """)

