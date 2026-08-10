from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Northstar | Canadian grocery expansion",
    page_icon=":material/storefront:",
    layout="wide",
)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "staging"
if not DATA.exists():
    DATA = ROOT

TEAL = "#087E72"
CORAL = "#D85C4A"
GOLD = "#D8A13A"
INK = "#172026"
SLATE = "#76838A"
GRID = "#DDD8CC"

PROVINCE_COORDS = {
    "Newfoundland and Labrador": (53.2, -60.2),
    "Prince Edward Island": (46.4, -63.4),
    "Nova Scotia": (45.1, -63.0),
    "New Brunswick": (46.6, -66.5),
    "Quebec": (52.0, -71.5),
    "Ontario": (50.0, -85.0),
    "Manitoba": (54.5, -98.0),
    "Saskatchewan": (54.0, -106.0),
    "Alberta": (54.5, -115.0),
    "British Columbia": (54.0, -125.0),
}


@st.cache_data(show_spinner=False)
def load_data():
    frames = {}
    for path in DATA.glob("*.csv"):
        frames[path.stem] = pd.read_csv(path)
    for name in ("DimDate", "FactFoodPrices", "FactPopulation", "FactRetailSales"):
        if "Date" in frames[name]:
            frames[name]["Date"] = pd.to_datetime(frames[name]["Date"])
    return frames


def minmax(series):
    lo, hi = series.min(), series.max()
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(50.0, index=series.index)
    return 100 * (series - lo) / (hi - lo)


def build_market_scores(frames, weights):
    geo = frames["DimGeography"].copy()
    food = frames["FactFoodPrices"].copy()
    products = frames["DimProduct"][["Product", "BasketWeight"]]
    population = frames["FactPopulation"].copy()
    income = frames["FactIncome"].copy()
    retail = frames["FactRetailSales"].copy()

    provinces = sorted(food["Geography"].dropna().unique())
    geo = geo[geo["Geography"].isin(provinces)]

    latest_food_date = food["Date"].max()
    latest_food = food[food["Date"].eq(latest_food_date)].merge(products, on="Product", how="left")
    basket = (
        latest_food.assign(Component=lambda d: d["Price"] * d["BasketWeight"])
        .groupby("Geography", as_index=False)["Component"]
        .sum()
        .rename(columns={"Component": "Basket cost"})
    )

    pop_rows = []
    for province, group in population[population["Geography"].isin(provinces)].groupby("Geography"):
        group = group.sort_values("Date")
        latest = group.iloc[-1]
        prior_candidates = group[group["Date"] <= latest["Date"] - pd.DateOffset(years=1)]
        prior = prior_candidates.iloc[-1] if not prior_candidates.empty else group.iloc[0]
        pop_rows.append(
            {
                "Geography": province,
                "Population": latest["Population"],
                "Population growth": latest["Population"] / prior["Population"] - 1,
                "Population date": latest["Date"],
            }
        )
    pop = pd.DataFrame(pop_rows)

    latest_income_year = int(income["Year"].max())
    inc = (
        income[(income["Year"] == latest_income_year) & income["Geography"].isin(provinces)]
        [["Geography", "MedianAfterTaxIncome"]]
        .rename(columns={"MedianAfterTaxIncome": "Median income"})
    )

    retail_end = retail["Date"].max()
    retail_start = retail_end - pd.DateOffset(months=11)
    retail_12m = (
        retail[retail["Date"].between(retail_start, retail_end) & retail["Geography"].isin(provinces)]
        .groupby("Geography", as_index=False)["RetailSalesThousands"]
        .sum()
        .rename(columns={"RetailSalesThousands": "Retail sales"})
    )
    retail_12m["Retail sales"] *= 1000

    market = geo.merge(basket, on="Geography").merge(pop, on="Geography").merge(inc, on="Geography").merge(retail_12m, on="Geography")
    market["Sales per capita"] = market["Retail sales"] / market["Population"]
    market["Basket burden"] = market["Basket cost"] * 52 / market["Median income"]
    market["Population momentum"] = minmax(market["Population growth"])
    market["Demand"] = minmax(market["Sales per capita"])
    market["Purchasing power"] = minmax(market["Median income"])
    market["Affordability opportunity"] = minmax(market["Basket burden"])
    market["Opportunity score"] = (
        weights["Population momentum"] * market["Population momentum"]
        + weights["Demand"] * market["Demand"]
        + weights["Purchasing power"] * market["Purchasing power"]
        + weights["Affordability opportunity"] * market["Affordability opportunity"]
    )
    market["Rank"] = market["Opportunity score"].rank(ascending=False, method="dense").astype(int)
    market["Latitude"] = market["Geography"].map(lambda x: PROVINCE_COORDS[x][0])
    market["Longitude"] = market["Geography"].map(lambda x: PROVINCE_COORDS[x][1])
    return market.sort_values("Rank"), latest_food_date, latest_income_year, retail_end


def price_pressure(frames, province):
    food = frames["FactFoodPrices"]
    products = frames["DimProduct"][["Product", "BasketCategory", "BasketWeight"]]
    p = food[food["Geography"].eq(province)].copy()
    latest = p["Date"].max()
    prior_target = latest - pd.DateOffset(years=1)
    prior_date = p.loc[p["Date"] <= prior_target, "Date"].max()
    current = p[p["Date"].eq(latest)][["Product", "Price"]].rename(columns={"Price": "Current price"})
    prior = p[p["Date"].eq(prior_date)][["Product", "Price"]].rename(columns={"Price": "Prior price"})
    pressure = current.merge(prior, on="Product").merge(products, on="Product")
    pressure["Weighted annual change"] = (pressure["Current price"] - pressure["Prior price"]) * pressure["BasketWeight"]
    pressure["Price change"] = pressure["Current price"] / pressure["Prior price"] - 1
    return pressure.sort_values("Weighted annual change", ascending=False), latest, prior_date


frames = load_data()

with st.sidebar:
    st.title(":material/tune: Scenario controls")
    st.caption("Adjust how Northstar balances market momentum, demand, purchasing power and affordability pressure.")
    with st.form("scenario"):
        pop_w = st.slider("Population momentum", 0, 100, 25, 5)
        demand_w = st.slider("Grocery demand", 0, 100, 30, 5)
        power_w = st.slider("Purchasing power", 0, 100, 20, 5)
        affordability_w = st.slider("Affordability opportunity", 0, 100, 25, 5)
        submitted = st.form_submit_button("Apply scenario", icon=":material/refresh:", type="primary")
    total = pop_w + demand_w + power_w + affordability_w
    if total == 0:
        st.warning("Choose at least one non-zero weight.")
        total = 1
    st.caption(f"Weights are normalized automatically · Current total: {total}%")

weights = {
    "Population momentum": pop_w / total,
    "Demand": demand_w / total,
    "Purchasing power": power_w / total,
    "Affordability opportunity": affordability_w / total,
}
market, latest_food_date, latest_income_year, retail_end = build_market_scores(frames, weights)

with st.sidebar:
    province = st.selectbox("Focus province", market["Geography"], index=0)
    comparison = st.segmented_control("Comparison", ["All provinces", "Regional peers"], default="All provinces")
    if comparison == "Regional peers":
        region = market.loc[market["Geography"].eq(province), "Region"].iloc[0]
        display_market = market[market["Region"].eq(region)]
    else:
        display_market = market
    st.caption(f"Food prices: {latest_food_date:%b %Y} · Income: {latest_income_year} · Retail: trailing 12 months to {retail_end:%b %Y}")

selected = market.loc[market["Geography"].eq(province)].iloc[0]
leader = market.iloc[0]

st.caption("NORTHSTAR FOODS  /  STRATEGY & EXPANSION")
st.title("Canadian grocery affordability & market expansion intelligence")
st.markdown(
    f"**{leader['Geography']} leads the current expansion scenario** with an opportunity score of "
    f"**{leader['Opportunity score']:.1f}/100**. Select a province to understand the trade-off between growth, demand, purchasing power and affordability pressure."
)

with st.container(horizontal=True):
    st.metric("Market rank", f"#{selected['Rank']} · {province}", border=True)
    st.metric("Opportunity score", f"{selected['Opportunity score']:.1f} / 100", border=True)
    st.metric("Population growth", f"{selected['Population growth']:+.1%}", border=True)
    st.metric("Weekly basket", f"${selected['Basket cost']:,.2f}", border=True)
    st.metric("Sales per capita", f"${selected['Sales per capita']:,.0f}", border=True)

map_col, driver_col = st.columns([1.6, 1], gap="medium")
with map_col:
    with st.container(border=True, height=430):
        st.subheader("Where opportunity concentrates")
        st.caption("Bubble size and colour reflect the weighted opportunity score; select a province from the sidebar for its diagnostic.")
        map_chart = (
            alt.Chart(display_market)
            .mark_circle(opacity=0.88, stroke="white", strokeWidth=2)
            .encode(
                longitude=alt.Longitude("Longitude:Q"),
                latitude=alt.Latitude("Latitude:Q"),
                size=alt.Size("Opportunity score:Q", scale=alt.Scale(range=[500, 2600]), legend=None),
                color=alt.Color("Opportunity score:Q", scale=alt.Scale(domain=[0, 50, 100], range=[CORAL, GOLD, TEAL]), legend=None),
                tooltip=[
                    alt.Tooltip("Geography:N", title="Province"),
                    alt.Tooltip("Rank:Q", title="Rank"),
                    alt.Tooltip("Opportunity score:Q", title="Score", format=".1f"),
                    alt.Tooltip("Population growth:Q", title="Population growth", format=".1%"),
                    alt.Tooltip("Basket burden:Q", title="Annual basket burden", format=".1%"),
                ],
            )
            .properties(height=300)
            .project(type="mercator", center=[-96, 57], scale=380)
        )
        st.altair_chart(map_chart)

with driver_col:
    with st.container(border=True, height=430):
        st.subheader(f"Why {province} ranks #{selected['Rank']}")
        st.caption("Four normalized components explain the composite score.")
        driver_data = pd.DataFrame(
            {
                "Component": ["Population momentum", "Demand", "Purchasing power", "Affordability opportunity"],
                "Score": [selected["Population momentum"], selected["Demand"], selected["Purchasing power"], selected["Affordability opportunity"]],
            }
        )
        driver_chart = (
            alt.Chart(driver_data)
            .mark_bar(cornerRadiusEnd=4)
            .encode(
                y=alt.Y("Component:N", sort=None, title=None),
                x=alt.X("Score:Q", scale=alt.Scale(domain=[0, 100]), title=None),
                color=alt.Color("Score:Q", scale=alt.Scale(domain=[0, 50, 100], range=[CORAL, GOLD, TEAL]), legend=None),
                tooltip=["Component", alt.Tooltip("Score", format=".1f")],
            )
            .properties(height=220)
        )
        st.altair_chart(driver_chart)
        strengths = driver_data.sort_values("Score", ascending=False)["Component"].tolist()
        st.info(f"**Decision read:** {strengths[0]} is the strongest reason to enter. {strengths[-1]} is the main constraint to mitigate.", icon=":material/lightbulb:")

frontier_col, pressure_col = st.columns([1.35, 1], gap="medium")
with frontier_col:
    with st.container(border=True, height=460):
        st.subheader("Market frontier: growth versus grocery demand")
        st.caption("Upper-right provinces combine population momentum with stronger retail demand. Bubble size shows population; colour shows affordability pressure.")
        scatter = (
            alt.Chart(display_market)
            .mark_circle(opacity=0.82, stroke="white", strokeWidth=1.5)
            .encode(
                x=alt.X("Population growth:Q", axis=alt.Axis(format=".1%"), title="Population growth"),
                y=alt.Y("Sales per capita:Q", axis=alt.Axis(format="$,.0f"), title="Grocery sales per capita"),
                size=alt.Size("Population:Q", scale=alt.Scale(range=[180, 1800]), legend=None),
                color=alt.Color("Basket burden:Q", scale=alt.Scale(scheme="yelloworangered"), legend=alt.Legend(title="Basket burden")),
                tooltip=[
                    alt.Tooltip("Geography:N", title="Province"),
                    alt.Tooltip("Population growth:Q", format=".1%"),
                    alt.Tooltip("Sales per capita:Q", format="$,.0f"),
                    alt.Tooltip("Basket burden:Q", format=".1%"),
                ],
            )
            .properties(height=320)
        )
        labels = alt.Chart(display_market).mark_text(dy=-13, fontSize=11, color=INK).encode(x="Population growth:Q", y="Sales per capita:Q", text="ProvinceCode:N")
        st.altair_chart(scatter + labels)

with pressure_col:
    pressure, current_date, prior_date = price_pressure(frames, province)
    with st.container(border=True, height=460):
        st.subheader("Products driving basket pressure")
        st.caption(f"Weighted contribution to basket change, {prior_date:%b %Y}–{current_date:%b %Y}.")
        pressure_display = pressure.head(8).copy()
        pressure_chart = (
            alt.Chart(pressure_display)
            .mark_bar(cornerRadiusEnd=4)
            .encode(
                y=alt.Y("Product:N", sort="-x", title=None, axis=alt.Axis(labelLimit=175)),
                x=alt.X("Weighted annual change:Q", title="Weighted basket change ($)"),
                color=alt.condition("datum['Weighted annual change'] >= 0", alt.value(CORAL), alt.value(TEAL)),
                tooltip=["Product", alt.Tooltip("Price change:Q", format="+.1%"), alt.Tooltip("Weighted annual change:Q", format="$+.2f")],
            )
            .properties(height=320)
        )
        st.altair_chart(pressure_chart)

st.subheader("Ranked market decision table")
st.caption("Use the component bars to see whether each market wins on momentum, demand, household purchasing power or affordability pressure.")
table = market[["Rank", "Geography", "Region", "Opportunity score", "Population momentum", "Demand", "Purchasing power", "Affordability opportunity", "Basket burden"]].copy()
st.dataframe(
    table,
    hide_index=True,
    height=410,
    column_config={
        "Rank": st.column_config.NumberColumn("Rank", format="#%d", width="small", pinned=True),
        "Geography": st.column_config.TextColumn("Province", pinned=True),
        "Opportunity score": st.column_config.ProgressColumn("Opportunity", min_value=0, max_value=100, format="%.1f"),
        "Population momentum": st.column_config.ProgressColumn("Momentum", min_value=0, max_value=100, format="%.0f"),
        "Demand": st.column_config.ProgressColumn("Demand", min_value=0, max_value=100, format="%.0f"),
        "Purchasing power": st.column_config.ProgressColumn("Power", min_value=0, max_value=100, format="%.0f"),
        "Affordability opportunity": st.column_config.ProgressColumn("Affordability", min_value=0, max_value=100, format="%.0f"),
        "Basket burden": st.column_config.NumberColumn("Annual basket burden", format="percent"),
    },
)

with st.expander("Methodology, assumptions and data quality"):
    st.markdown(
        """
        - **Opportunity score:** weighted combination of four min-max normalized components. The score is a portfolio scenario, not an official Statistics Canada indicator.
        - **Representative basket:** latest available provincial food prices multiplied by the scenario weights in `DimProduct.csv`; displayed as a weekly planning assumption.
        - **Population:** latest quarterly estimate compared with the closest quarter at least one year earlier.
        - **Demand:** trailing 12-month retail sales, converted from thousands of dollars exactly once, divided by latest population.
        - **Income:** latest available annual median after-tax income. Annual and quarterly snapshots are never summed across dates.
        - **Coverage:** the default expansion ranking includes the ten provinces with comparable provincial food-price coverage.
        """
    )
