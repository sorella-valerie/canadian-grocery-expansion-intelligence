import streamlit as st

st.set_page_config(page_title="Rellatech data portfolio", page_icon=":material/analytics:", layout="wide")
st.title("Rellatech decision intelligence portfolio")
st.write("Six separate analytical experiences built from official public data and clearly labelled derived scenarios.")
st.caption("Each dashboard now has its own decision flow, visual grammar, evidence table, source vintage, and limitation statement.")

projects = [
    ("Canada affordability & opportunity explorer", "Compare take-home pay, rent, groceries, and occupation wages across ten cities.", "https://canada-affordability-opportunity.streamlit.app/", "location_city"),
    ("Canadian healthcare access map", "Explore the national footprint of hospitals, clinics, and long-term care facilities.", "https://canadian-healthcare-access.streamlit.app/", "local_hospital"),
    ("Newcomer settlement navigator", "Rank Canadian cities using household costs, local wages, and healthcare access.", "https://canada-newcomer-settlement.streamlit.app/", "travel_explore"),
    ("Canadian food affordability monitor", "See provincial grocery burden, price changes, and product-level pressure.", "https://canada-food-affordability.streamlit.app/", "shopping_basket"),
    ("Nonprofit sustainability dashboard", "Stress-test funding, expense growth, cash runway, and sector employment.", "https://nonprofit-sustainability.streamlit.app/", "volunteer_activism"),
    ("Global cost & opportunity explorer", "Screen twenty countries using purchasing power, jobs, inflation, and health investment.", "https://global-cost-opportunity.streamlit.app/", "public"),
]

for row in (projects[:3], projects[3:]):
    columns = st.columns(3)
    for column, (name, description, url, icon) in zip(columns, row):
        with column.container(border=True, height="stretch"):
            st.subheader(f":material/{icon}: {name}")
            st.write(description)
            st.link_button("Open dashboard", url, icon=":material/open_in_new:", type="primary")

with st.container(border=True):
    st.subheader("Evidence standard")
    st.write("Official published values are separated from local calculations and user scenarios. Weighted scores are transparent portfolio models, never presented as government indicators.")
    st.caption("The complete source and limitation register is stored in DATA_GOVERNANCE.md in the portfolio folder.")
