from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


ROOT = Path(__file__).parent

INDICATORS = {
    "GDP per capita, PPP": {
        "column": "income_ppp",
        "year": "income_ppp_year",
        "code": "NY.GDP.PCAP.PP.CD",
        "unit": "current international $",
        "higher": True,
    },
    "Unemployment rate": {
        "column": "unemployment",
        "year": "unemployment_year",
        "code": "SL.UEM.TOTL.ZS",
        "unit": "% of total labour force",
        "higher": False,
    },
    "Consumer-price inflation": {
        "column": "inflation",
        "year": "inflation_year",
        "code": "FP.CPI.TOTL.ZG",
        "unit": "annual %",
        "higher": False,
    },
    "Current health expenditure per person": {
        "column": "health_spend_pc",
        "year": "health_spend_pc_year",
        "code": "SH.XPD.CHEX.PC.CD",
        "unit": "current US$",
        "higher": True,
    },
}


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "world_bank_country_profiles.csv")


def money(value: float) -> str:
    return f"${value:,.0f}"


st.set_page_config(
    page_title="World Bank country indicators",
    page_icon=":material/public:",
    layout="wide",
)

data = load_data()

with st.sidebar:
    st.title("Official comparison")
    selected_country = st.selectbox(
        "Country to inspect",
        sorted(data["country"]),
        index=sorted(data["country"]).index("Canada"),
    )
    selected_indicator = st.selectbox("Rank countries by", list(INDICATORS))
    selected_countries = st.multiselect(
        "Countries to compare",
        sorted(data["country"]),
        default=sorted(data["country"]),
    )

comparison = data[data["country"].isin(selected_countries)].copy()
if len(comparison) < 2:
    st.warning("Select at least two countries for a meaningful comparison.", icon=":material/public:")
    st.stop()

definition = INDICATORS[selected_indicator]
comparison = comparison.sort_values(
    definition["column"], ascending=not definition["higher"]
).reset_index(drop=True)
comparison["rank"] = comparison.index + 1

leader = comparison.iloc[0]
chosen = comparison[comparison["country"].eq(selected_country)]
chosen = chosen.iloc[0] if not chosen.empty else leader

st.title("World Bank country opportunity indicators")
st.write(
    "Compare economic output, labour-market conditions, price change and health expenditure using official World Bank indicators."
)
st.caption(
    "Every numeric value is the latest available observation from the World Bank Indicators API for 2021 to 2025. The selected indicator alone determines the country order."
)

with st.container(border=True):
    chosen_rank = int(chosen["rank"])
    chosen_value = chosen[definition["column"]]
    leader_value = leader[definition["column"]]
    st.subheader(
        f"{chosen.country} ranks {chosen_rank} of {len(comparison)} by {selected_indicator.lower()}."
    )
    if chosen.country == leader.country:
        st.write(
            f"{chosen.country} leads the selected comparison at {chosen_value:,.1f} {definition['unit']}."
        )
    else:
        st.write(
            f"{leader.country} leads at {leader_value:,.1f} {definition['unit']}. {chosen.country} records {chosen_value:,.1f}."
        )

with st.container(horizontal=True):
    st.metric(
        "GDP per capita, PPP",
        money(chosen.income_ppp),
        f"World Bank {int(chosen.income_ppp_year)}",
        border=True,
    )
    st.metric(
        "Unemployment rate",
        f"{chosen.unemployment:.1f}%",
        f"World Bank {int(chosen.unemployment_year)}",
        border=True,
    )
    st.metric(
        "Consumer-price inflation",
        f"{chosen.inflation:.1f}%",
        f"World Bank {int(chosen.inflation_year)}",
        border=True,
    )
    st.metric(
        "Health expenditure per person",
        money(chosen.health_spend_pc),
        f"World Bank {int(chosen.health_spend_pc_year)}",
        border=True,
    )

st.subheader("What the official indicators show")
left, right = st.columns(2)

with left.container(border=True):
    st.markdown(f"**Country order by {selected_indicator.lower()}**")
    rank_chart = (
        alt.Chart(comparison.head(15))
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            x=alt.X(
                f"{definition['column']}:Q",
                title=f"{selected_indicator} ({definition['unit']})",
            ),
            y=alt.Y("country:N", sort=comparison["country"].head(15).tolist(), title=None),
            color=alt.condition(
                f"datum.country == '{chosen.country}'",
                alt.value("#C65310"),
                alt.value("#153A47"),
            ),
            tooltip=[
                "country",
                alt.Tooltip(definition["column"], title=selected_indicator, format=",.1f"),
                alt.Tooltip(definition["year"], title="Observation year"),
            ],
        )
        .properties(height=330)
    )
    st.altair_chart(rank_chart)
    st.caption(
        f"The order uses only World Bank indicator {definition['code']}. No composite score or normalized rating is used."
    )

with right.container(border=True):
    st.markdown("**Economic output and unemployment**")
    frontier = (
        alt.Chart(comparison)
        .mark_circle(opacity=0.85)
        .encode(
            x=alt.X("unemployment:Q", title="Unemployment rate (%)"),
            y=alt.Y(
                "income_ppp:Q",
                title="GDP per capita, PPP (international $)",
                scale=alt.Scale(zero=False),
            ),
            size=alt.Size(
                "health_spend_pc:Q",
                title="Health expenditure per person",
                scale=alt.Scale(range=[100, 900]),
            ),
            color=alt.condition(
                f"datum.country == '{chosen.country}'",
                alt.value("#C65310"),
                alt.value("#153A47"),
            ),
            tooltip=[
                "country",
                alt.Tooltip("income_ppp", title="GDP per capita, PPP", format="$,.0f"),
                alt.Tooltip("unemployment", title="Unemployment", format=".1f"),
                alt.Tooltip("health_spend_pc", title="Health expenditure", format="$,.0f"),
            ],
        )
        .properties(height=330)
    )
    st.altair_chart(frontier)
    st.caption(
        "Higher positions show greater GDP per capita, PPP. Positions farther left show lower unemployment. Bubble size is health expenditure per person."
    )

pressure_left, health_right = st.columns(2)
with pressure_left.container(border=True):
    st.markdown("**Inflation and unemployment**")
    pressure = (
        alt.Chart(comparison)
        .mark_circle(size=170)
        .encode(
            x=alt.X("inflation:Q", title="Consumer-price inflation (annual %)"),
            y=alt.Y("unemployment:Q", title="Unemployment rate (%)"),
            color=alt.condition(
                f"datum.country == '{chosen.country}'",
                alt.value("#C65310"),
                alt.value("#153A47"),
            ),
            tooltip=[
                "country",
                alt.Tooltip("inflation", format=".1f"),
                alt.Tooltip("unemployment", format=".1f"),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(pressure)
    st.caption(
        f"{chosen.country} records {chosen.inflation:.1f}% inflation and {chosen.unemployment:.1f}% unemployment in the latest available World Bank observations."
    )

with health_right.container(border=True):
    st.markdown("**Health expenditure per person**")
    health = (
        alt.Chart(comparison.sort_values("health_spend_pc", ascending=False).head(15))
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            x=alt.X("health_spend_pc:Q", title="Current US$ per person"),
            y=alt.Y("country:N", sort="-x", title=None),
            color=alt.condition(
                f"datum.country == '{chosen.country}'",
                alt.value("#C65310"),
                alt.value("#153A47"),
            ),
            tooltip=[
                "country",
                alt.Tooltip("health_spend_pc", format="$,.0f"),
                alt.Tooltip("health_spend_pc_year", title="Observation year"),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(health)
    st.caption(
        "This is current health expenditure per capita in current US dollars, as published through the World Bank indicator service."
    )

evidence_tab, definitions_tab = st.tabs(["Official evidence", "Indicator definitions"])
with evidence_tab:
    evidence = comparison[
        [
            "rank",
            "country",
            "income_ppp",
            "income_ppp_year",
            "unemployment",
            "unemployment_year",
            "inflation",
            "inflation_year",
            "health_spend_pc",
            "health_spend_pc_year",
        ]
    ].copy()
    evidence.columns = [
        "Selected indicator rank",
        "Country",
        "GDP per capita, PPP",
        "GDP year",
        "Unemployment rate",
        "Unemployment year",
        "Consumer-price inflation",
        "Inflation year",
        "Health expenditure per person",
        "Health year",
    ]
    st.dataframe(
        evidence,
        hide_index=True,
        key="world_bank_evidence",
        column_config={
            "GDP per capita, PPP": st.column_config.NumberColumn(format="$%.0f"),
            "Unemployment rate": st.column_config.NumberColumn(format="%.1f%%"),
            "Consumer-price inflation": st.column_config.NumberColumn(format="%.1f%%"),
            "Health expenditure per person": st.column_config.NumberColumn(format="$%.0f"),
        },
    )

with definitions_tab:
    st.markdown(
        """
| World Bank indicator | Code | Unit |
|---|---|---|
| GDP per capita, PPP | `NY.GDP.PCAP.PP.CD` | Current international dollars |
| Unemployment, total | `SL.UEM.TOTL.ZS` | Percent of total labour force, modeled ILO estimate |
| Inflation, consumer prices | `FP.CPI.TOTL.ZG` | Annual percent |
| Current health expenditure per capita | `SH.XPD.CHEX.PC.CD` | Current US dollars |
"""
    )
    st.info(
        "GDP per capita, PPP measures economic output per person. It is not household income. Inflation measures price change, not the absolute cost of living in a city.",
        icon=":material/info:",
    )

with st.expander("World Bank source", icon=":material/database:"):
    st.write(
        "Source: World Bank Indicators API. Each country uses the latest non-null observation returned for 2021 to 2025."
    )
    for label, item in INDICATORS.items():
        st.link_button(
            f"Open {label}",
            f"https://data.worldbank.org/indicator/{item['code']}",
            icon=":material/open_in_new:",
        )
