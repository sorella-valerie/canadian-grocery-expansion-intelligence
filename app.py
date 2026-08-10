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

TEAL = "#153A47"
CORAL = "#C65310"
GOLD = "#D99A68"
INK = "#141D29"
SLATE = "#78909C"
GRID = "#E3E9EB"

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
st.caption("Official Statistics Canada population, grocery sales, income and food-price data, combined into an adjustable scenario score for comparing provincial opportunities.")
st.markdown(
    f"**{leader['Geography']} leads the current expansion scenario** with an opportunity score of "
    f"**{leader['Opportunity score']:.1f}/100**. Select a province to understand the trade-off between growth, demand, purchasing power and affordability pressure."
)

population_spark = frames["FactPopulation"].loc[
    frames["FactPopulation"]["Geography"].eq(province)
].sort_values("Date").tail(8)["Population"].tolist()
sales_spark = frames["FactRetailSales"].loc[
    frames["FactRetailSales"]["Geography"].eq(province)
].sort_values("Date").tail(12)["RetailSalesThousands"].tolist()
basket_spark = (
    frames["FactFoodPrices"].loc[frames["FactFoodPrices"]["Geography"].eq(province)]
    .merge(frames["DimProduct"][["Product", "BasketWeight"]], on="Product", how="inner")
    .assign(WeightedPrice=lambda data: data["Price"] * data["BasketWeight"])
    .groupby("Date", as_index=False)["WeightedPrice"].sum()
    .sort_values("Date").tail(12)["WeightedPrice"].tolist()
)

with st.container(horizontal=True):
    st.metric(
        "Opportunity score", f"{selected['Opportunity score']:.1f} / 100",
        f"Rank #{selected['Rank']} in Canada", delta_color="off", border=True,
        chart_data=[selected["Population momentum"], selected["Demand"], selected["Purchasing power"], selected["Affordability opportunity"]],
        chart_type="bar",
    )
    st.metric(
        "Population growth", f"{selected['Population growth']:+.1%}",
        "Latest annual change", delta_color="off", border=True, chart_data=population_spark, chart_type="line",
    )
    st.metric(
        "Grocery sales per resident", f"${selected['Sales per capita']:,.0f}",
        "Trailing 12 months", delta_color="off", border=True, chart_data=sales_spark, chart_type="bar",
    )
    st.metric(
        "Weekly basket", f"${selected['Basket cost']:,.2f}",
        "Latest planning basket", delta_color="off", border=True, chart_data=basket_spark, chart_type="line",
    )

runner_up = market.iloc[1]
score_gap = leader["Opportunity score"] - runner_up["Opportunity score"]
st.subheader("Where should Northstar expand?")
st.caption(
    f"{leader['Geography']} ranks first, {score_gap:.1f} points ahead of {runner_up['Geography']}. "
    "The ranking changes when you adjust the strategy weights in the sidebar."
)

map_col, driver_col = st.columns([1.6, 1], gap="medium")
with map_col:
    with st.container(border=True, height=500):
        st.subheader("Expansion opportunity ranking")
        st.caption("Longer bars indicate a stronger overall fit across growth, demand, income and affordability.")
        rank_data = display_market.sort_values("Opportunity score", ascending=True).copy()
        rank_data["Highlight"] = np.where(
            rank_data["Geography"].eq(province),
            "Selected province",
            np.where(rank_data["Rank"].eq(1), "Scenario leader", "Other provinces"),
        )
        ranking_chart = (
            alt.Chart(rank_data)
            .mark_bar(cornerRadiusEnd=5, height=18)
            .encode(
                y=alt.Y("Geography:N", sort=alt.SortField("Opportunity score", order="descending"), title=None),
                x=alt.X("Opportunity score:Q", scale=alt.Scale(domain=[0, 100]), title="Opportunity score (0–100)"),
                color=alt.Color(
                    "Highlight:N",
                    scale=alt.Scale(
                        domain=["Scenario leader", "Selected province", "Other provinces"],
                        range=[TEAL, CORAL, "#CBD1CF"],
                    ),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("Geography:N", title="Province"),
                    alt.Tooltip("Rank:Q", title="Rank"),
                    alt.Tooltip("Opportunity score:Q", title="Score", format=".1f"),
                ],
            )
            .properties(height=300)
        )
        score_labels = alt.Chart(rank_data).mark_text(align="left", dx=6, fontSize=11, color=INK).encode(
            y=alt.Y("Geography:N", sort=alt.SortField("Opportunity score", order="descending")),
            x="Opportunity score:Q",
            text=alt.Text("Opportunity score:Q", format=".1f"),
        )
        st.altair_chart(ranking_chart + score_labels)

with driver_col:
    with st.container(border=True, height=500):
        st.subheader(f"Why {province} ranks #{selected['Rank']}")
        driver_data = pd.DataFrame(
            {
                "Component": ["Population momentum", "Demand", "Purchasing power", "Affordability opportunity"],
                "Score": [selected["Population momentum"], selected["Demand"], selected["Purchasing power"], selected["Affordability opportunity"]],
            }
        )
        strongest_driver = driver_data.loc[driver_data["Score"].idxmax()]
        weakest_driver = driver_data.loc[driver_data["Score"].idxmin()]
        strength_context = {
            "Population momentum": f"Annual population growth of {selected['Population growth']:+.1%} supports an expanding customer base.",
            "Demand": f"Grocery sales of ${selected['Sales per capita']:,.0f} per resident signal comparatively strong spending.",
            "Purchasing power": f"Median after-tax income of ${selected['Median income']:,.0f} provides stronger household spending capacity.",
            "Affordability opportunity": f"A {selected['Basket burden']:.1%} annual basket burden creates a clear opening for a value-led offer.",
        }
        weakness_context = {
            "Population momentum": f"Annual population growth of {selected['Population growth']:+.1%} limits near-term customer-base expansion.",
            "Demand": f"Grocery sales of ${selected['Sales per capita']:,.0f} per resident trail stronger markets, so revenue assumptions should stay conservative.",
            "Purchasing power": f"Median after-tax income of ${selected['Median income']:,.0f} reduces pricing headroom and increases sensitivity to premium positioning.",
            "Affordability opportunity": f"A {selected['Basket burden']:.1%} annual basket burden suggests less urgency for an affordability-first proposition.",
        }
        st.markdown(
            f"**Strength: {strongest_driver['Component']} ({strongest_driver['Score']:.0f}/100).** "
            f"{strength_context[strongest_driver['Component']]}\n\n"
            f"**Constraint: {weakest_driver['Component']} ({weakest_driver['Score']:.0f}/100).** "
            f"{weakness_context[weakest_driver['Component']]}"
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

st.subheader("Pressure-test the opportunity")
st.caption("A strong market needs both customer growth and grocery spending, with a clear plan for the products creating price pressure.")

frontier_col, pressure_col = st.columns([1.15, 1], gap="medium")
with frontier_col:
    with st.container(border=True, height=460):
        st.subheader("Market momentum across Canada")
        st.caption("Bubble size shows grocery sales per resident. Orange marks provinces above both the growth and demand medians.")
        median_growth = float(display_market["Population growth"].median())
        median_demand = float(display_market["Sales per capita"].median())
        frontier_data = display_market.copy()
        frontier_data["Market position"] = np.where(
            (frontier_data["Population growth"] >= median_growth)
            & (frontier_data["Sales per capita"] >= median_demand),
            "High growth + high demand",
            "Other provinces",
        )
        frontier_data["Map size"] = 65000 + 340000 * (
            frontier_data["Sales per capita"] / frontier_data["Sales per capita"].max()
        )
        frontier_data["Map color"] = np.where(
            frontier_data["Market position"].eq("High growth + high demand"), CORAL, TEAL
        )
        st.map(
            frontier_data,
            latitude="Latitude",
            longitude="Longitude",
            size="Map size",
            color="Map color",
            zoom=2,
            height=300,
        )
        frontier_names = ", ".join(
            frontier_data.loc[frontier_data["Market position"].eq("High growth + high demand"), "ProvinceCode"]
        )
        st.caption(f"**Above both medians:** {frontier_names}. These markets show the clearest combination of momentum and demand.")

with pressure_col:
    pressure, current_date, prior_date = price_pressure(frames, province)
    with st.container(border=True, height=460):
        st.subheader("What changed the weekly basket?")
        st.caption(f"Dollar impact by product in {province}, {prior_date:%b %Y} to {current_date:%b %Y}.")
        pressure_display = pressure.head(8).copy()
        pressure_display["Product label"] = pressure_display["Product"].str.split(",").str[0]
        pressure_display["Price direction"] = np.where(
            pressure_display["Weighted annual change"] >= 0,
            "Raised basket cost",
            "Lowered basket cost",
        )
        pressure_display = pressure_display.sort_values("Weighted annual change", ascending=True)
        st.bar_chart(
            pressure_display,
            x="Product label",
            y="Weighted annual change",
            horizontal=True,
            color=CORAL,
            x_label="Weekly basket impact ($)",
            y_label="",
            height=285,
        )
        top_pressure = pressure_display.loc[pressure_display["Weighted annual change"].abs().idxmax()]
        direction = "increased" if top_pressure["Weighted annual change"] >= 0 else "reduced"
        st.caption(
            f"**Biggest basket mover:** {top_pressure['Product']} {direction} the weighted basket by "
            f"${abs(top_pressure['Weighted annual change']):.2f}."
        )

st.subheader("Compare the evidence")
st.caption("The full ranking shows whether each province's score is balanced or depends heavily on one advantage.")
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

with st.expander("Real data, methodology and limitations"):
    st.markdown(
        """
        The underlying observations are real public data. Only the basket definition and opportunity-score weights are planning assumptions.

        - **Food prices, observed data:** Statistics Canada table [18-10-0245-02](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810024502), monthly average retail prices for selected foods. The representative basket multiplies the latest provincial prices by the documented quantities in `DimProduct.csv`; it is a weekly planning basket, not an official cost-of-food measure.
        - **Population, observed data:** Statistics Canada table [17-10-0009-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1710000901). Growth compares the latest quarterly estimate with the closest quarter at least one year earlier.
        - **Grocery demand, observed data:** Statistics Canada table [20-10-0056-02](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010005602). Trailing 12-month retail sales are converted from thousands of dollars once, then divided by the latest population estimate.
        - **Income, observed data:** Statistics Canada table [11-10-0091-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1110009101). The dashboard uses the latest annual median after-tax income; annual and quarterly snapshots are never summed across dates.
        - **Opportunity score, scenario model:** four min-max normalized components combined using the visible sidebar weights. It is an original portfolio decision model, not a Statistics Canada indicator.
        - **Coverage:** the ranking includes the ten provinces with comparable provincial food-price coverage. Territories are excluded from the default comparison.
        """
    )
