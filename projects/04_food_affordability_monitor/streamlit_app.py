from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st

ROOT=Path(__file__).parent
@st.cache_data
def load():
    food=pd.read_csv(ROOT/'data/FactFoodPrices.csv',parse_dates=['Date'])
    products=pd.read_csv(ROOT/'data/DimProduct.csv')
    income=pd.read_csv(ROOT/'data/FactIncome.csv')
    return food.merge(products,on='Product'),income

st.set_page_config(page_title="Canadian food affordability monitor",page_icon=":material/shopping_basket:",layout="wide")
food,income=load(); provinces=sorted(food.Geography.unique())
with st.sidebar:
    st.title("Basket controls")
    selected=st.multiselect("Provinces",provinces,default=provinces)
    household=st.number_input("Household multiplier",1,6,1)
    category=st.multiselect("Basket categories",sorted(food.BasketCategory.unique()),default=sorted(food.BasketCategory.unique()))
    focus=st.selectbox("Province to inspect",selected if selected else provinces)

if not selected or not category:
    st.warning("Select at least one province and one basket category.",icon=":material/filter_alt:")
    st.stop()

f=food[food.Geography.isin(selected)&food.BasketCategory.isin(category)].copy()
f['weighted']=f.Price*f.BasketWeight*household
basket=f.groupby(['Date','Geography'],as_index=False).weighted.sum(); latest_date=basket.Date.max(); year_ago=latest_date-pd.DateOffset(years=1)
latest=basket[basket.Date.eq(latest_date)].rename(columns={'weighted':'weekly_basket'})
prior=basket[basket.Date.le(year_ago)].sort_values('Date').groupby('Geography').tail(1)[['Geography','weighted']].rename(columns={'weighted':'prior_basket'})
rank=latest.merge(prior,on='Geography'); rank['change_pct']=rank.weekly_basket/rank.prior_basket-1
inc=income.sort_values('Year').groupby('Geography').tail(1)[['Geography','MedianAfterTaxIncome']]
rank=rank.merge(inc,on='Geography',how='left'); rank['annual_basket']=rank.weekly_basket*52; rank['income_share']=rank.annual_basket/rank.MedianAfterTaxIncome
rank=rank.sort_values('income_share'); best=rank.iloc[0]; worst=rank.iloc[-1]

st.title("Canadian food affordability monitor")
st.write("Track what a representative grocery basket costs, what is driving the change, and how much household income it absorbs.")
st.caption(f"Official Statistics Canada prices through {latest_date:%B %Y}. The basket quantities, household multiplier, affordability burden, and contribution analysis are derived here.")
with st.container(border=True):
    st.subheader(f"Food is most affordable relative to income in {best.Geography}, where this basket uses {best.income_share:.1%} of median after-tax income.")
    st.caption(f"{worst.Geography} has the highest burden at {worst.income_share:.1%}. That is a {worst.income_share-best.income_share:.1%} point gap for the same basket design.")

cols=st.columns(4)
focus_row=rank[rank.Geography.eq(focus)].iloc[0]
cols[0].metric("Derived weekly basket",f"${focus_row.weekly_basket:,.2f}",f"{focus_row.change_pct:+.1%} YoY",border=True)
cols[1].metric("Official median income",f"${focus_row.MedianAfterTaxIncome:,.0f}",border=True)
cols[2].metric("Derived income burden",f"{focus_row.income_share:.1%}",border=True)
cols[3].metric("Provincial spread",f"${rank.weekly_basket.max()-rank.weekly_basket.min():,.2f}",border=True)

summary_trend=basket[basket.Geography.eq(focus)].sort_values('Date')
summary_latest=f[f.Date.eq(latest_date)][['Geography','Product','BasketCategory','weighted']]
summary_prior=f[f.Date.le(year_ago)].sort_values('Date').groupby(['Geography','Product']).tail(1)[['Geography','Product','weighted']].rename(columns={'weighted':'prior'})
summary_drivers=summary_latest.merge(summary_prior,on=['Geography','Product']); summary_drivers['impact']=summary_drivers.weighted-summary_drivers.prior
summary_drivers=summary_drivers[summary_drivers.Geography.eq(focus)].sort_values('impact',ascending=False).head(10)
st.subheader("What the selected prices show")
top_left,top_right=st.columns(2)
with top_left.container(border=True):
    st.markdown(f"**{focus} basket trend**")
    st.altair_chart(alt.Chart(summary_trend).mark_line(color='#153A47',strokeWidth=3).encode(x=alt.X('Date:T',title=None),y=alt.Y('weighted:Q',title='Weekly basket ($)',scale=alt.Scale(zero=False)),tooltip=[alt.Tooltip('Date:T',format='%b %Y'),alt.Tooltip('weighted',format='$,.2f')]),height=270)
    st.caption(f"The {focus} basket is ${focus_row.weekly_basket:,.2f}. The 12-month change is {focus_row.change_pct:+.1%}.")
with top_right.container(border=True):
    st.markdown("**Affordability burden**")
    st.altair_chart(alt.Chart(rank).mark_bar(cornerRadiusEnd=5).encode(x=alt.X('income_share:Q',axis=alt.Axis(format='%'),title='Basket share of income'),y=alt.Y('Geography:N',sort='x',title=None),color=alt.condition(f"datum.Geography == '{focus}'",alt.value('#C65310'),alt.value('#153A47')),tooltip=['Geography',alt.Tooltip('income_share',format='.1%')]),height=270)
    st.caption(f"The basket uses {focus_row.income_share:.1%} of {focus}'s median after-tax income. The provincial range is {best.income_share:.1%} to {worst.income_share:.1%}.")
bottom_left,bottom_right=st.columns(2)
with bottom_left.container(border=True):
    st.markdown("**Annual provincial price change**")
    st.altair_chart(alt.Chart(rank).mark_bar(cornerRadiusEnd=5).encode(x=alt.X('change_pct:Q',axis=alt.Axis(format='%'),title='Change versus prior year'),y=alt.Y('Geography:N',sort='-x',title=None),color=alt.condition('datum.change_pct > 0',alt.value('#C65310'),alt.value('#29747A')),tooltip=['Geography',alt.Tooltip('change_pct',format='.1%')]),height=270)
    st.caption(f"{rank.loc[rank.change_pct.idxmax(),'Geography']} has the largest increase at {rank.change_pct.max():.1%}.")
with bottom_right.container(border=True):
    st.markdown("**Largest product contributions**")
    st.altair_chart(alt.Chart(summary_drivers).mark_bar(cornerRadiusEnd=5).encode(x=alt.X('impact:Q',title='Weekly contribution ($)'),y=alt.Y('Product:N',sort='-x',title=None),color=alt.condition('datum.impact > 0',alt.value('#C65310'),alt.value('#29747A')),tooltip=['Product',alt.Tooltip('impact',format='$,.2f')]),height=270)
    st.caption(f"{summary_drivers.iloc[0].Product} adds the most to the weekly change at ${summary_drivers.iloc[0].impact:,.2f}.")

trend_tab, burden_tab, drivers_tab, evidence_tab=st.tabs(["Basket trend","Affordability gap","Product pressure","Official evidence"])
with trend_tab:
    st.subheader(f"How the basket changed in {focus}")
    focus_trend=basket[basket.Geography.eq(focus)].sort_values('Date')
    focus_trend['Index']=focus_trend.weighted/focus_trend.weighted.iloc[0]*100
    line=alt.Chart(focus_trend).mark_line(color='#153A47',strokeWidth=3).encode(x=alt.X('Date:T',title=None),y=alt.Y('weighted:Q',title='Derived weekly basket ($)',scale=alt.Scale(zero=False)),tooltip=[alt.Tooltip('Date:T',format='%b %Y'),alt.Tooltip('weighted',format='$,.2f')])
    st.altair_chart(line)
    monthly=focus_trend.set_index('Date').weighted.pct_change(12).dropna()
    st.metric("Latest 12-month basket change",f"{monthly.iloc[-1]:+.1%}" if len(monthly) else "Not available")

with burden_tab:
    left,right=st.columns(2)
    with left.container(border=True):
        st.subheader("Income burden")
        st.altair_chart(alt.Chart(rank).mark_bar(cornerRadiusEnd=5).encode(x=alt.X('income_share:Q',axis=alt.Axis(format='%'),title='Annual basket share of income'),y=alt.Y('Geography:N',sort='x',title=None),color=alt.condition(f"datum.Geography == '{focus}'",alt.value('#C65310'),alt.value('#153A47')),tooltip=['Geography',alt.Tooltip('income_share',format='.1%')]))
    with right.container(border=True):
        st.subheader("Annual price change")
        st.altair_chart(alt.Chart(rank).mark_bar(cornerRadiusEnd=5).encode(x=alt.X('change_pct:Q',axis=alt.Axis(format='%'),title='Change versus one year earlier'),y=alt.Y('Geography:N',sort='-x',title=None),color=alt.condition('datum.change_pct > 0',alt.value('#C65310'),alt.value('#29747A')),tooltip=['Geography',alt.Tooltip('change_pct',format='.1%')]))

with drivers_tab:
    latest_prod=f[f.Date.eq(latest_date)][['Geography','Product','BasketCategory','weighted']]
    prior_prod=f[f.Date.le(year_ago)].sort_values('Date').groupby(['Geography','Product']).tail(1)[['Geography','Product','weighted']].rename(columns={'weighted':'prior'})
    drivers=latest_prod.merge(prior_prod,on=['Geography','Product']); drivers['impact']=drivers.weighted-drivers.prior
    focused=drivers[drivers.Geography.eq(focus)].sort_values('impact',ascending=False)
    st.subheader(f"What moved the {focus} basket")
    st.altair_chart(alt.Chart(focused).mark_bar(cornerRadiusEnd=5).encode(x=alt.X('impact:Q',title='Derived weekly contribution to change ($)'),y=alt.Y('Product:N',sort='-x',title=None),color=alt.condition('datum.impact > 0',alt.value('#C65310'),alt.value('#29747A')),tooltip=['Product','BasketCategory',alt.Tooltip('impact',format='$,.2f')]))

with evidence_tab:
    official=f[f.Date.eq(latest_date)][['Geography','Product','BasketCategory','Price','BasketWeight']].copy()
    official.columns=['Province','Official product','Category','Official price','Scenario quantity']
    st.dataframe(official,hide_index=True,key='food_evidence',column_config={'Official price':st.column_config.NumberColumn(format='$%.2f'),'Scenario quantity':st.column_config.NumberColumn(format='%.2f')})

with st.expander("Method and sources",icon=":material/database:"):
    st.markdown("Prices: Statistics Canada table 18-10-0245-02. Income: latest annual median after-tax income snapshot. Annual income is never summed across years. Weekly basket costs are the latest provincial prices multiplied by the visible product weights.")

