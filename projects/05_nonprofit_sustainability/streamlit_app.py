from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st

ROOT=Path(__file__).parent
@st.cache_data
def load():
    d=pd.read_csv(ROOT/'data/raw/employment_activity/36100615.csv',low_memory=False)
    return d[(d['Sub-sector']=='Total non-profit institutions')&(d.Activity!='Total activities')].copy()

st.set_page_config(page_title='Nonprofit sustainability dashboard',page_icon=':material/volunteer_activism:',layout='wide')
d=load(); activities=sorted(d.Activity.unique())
with st.sidebar:
    st.title('Organization scenario')
    activity=st.selectbox('Mission area',activities,index=activities.index('Social services'))
    revenue=st.number_input('Annual unrestricted revenue',min_value=10000,value=750000,step=10000)
    expenses=st.number_input('Annual operating expenses',min_value=10000,value=800000,step=10000)
    cash=st.number_input('Available cash reserves',min_value=0,value=180000,step=10000)
    annual_growth=st.slider('Expected expense growth',0.0,20.0,6.0,.5)/100

monthly_exp=expenses/12; deficit=max(expenses-revenue,0); runway=cash/monthly_exp if monthly_exp else 0
next_exp=expenses*(1+annual_growth); next_gap=revenue-next_exp
gap_text=f"-${abs(next_gap):,.0f}" if next_gap < 0 else f"${next_gap:,.0f}"
if runway<3 or next_gap<-(expenses*.1): status='High risk'
elif runway<6 or next_gap<0: status='Watch closely'
else: status='Resilient'

sector=d[(d.GEO=='Canada')&(d.Activity==activity)].sort_values('REF_DATE')
latest=sector.iloc[-1]; prior=sector.iloc[-2]; jobs=latest.VALUE*1000; job_change=latest.VALUE/prior.VALUE-1

st.title('Nonprofit sustainability dashboard')
st.write('Test revenue, expenses, reserves, and sector employment context.')
st.caption('Official Statistics Canada sector employment through 2024. Organization finances, runway, thresholds, stress tests, and risk labels are user-controlled planning scenarios.')
with st.container(border=True):
    if next_gap<0:
        st.subheader(f'{status}: next year projected funding gap is ${abs(next_gap):,.0f}. Reserves cover {runway:.1f} months.')
        st.caption(f'The immediate decision is to close the gap, slow expense growth, or protect at least six months of operating cash.')
    else:
        st.subheader(f'{status}: the scenario produces a ${next_gap:,.0f} cushion next year and {runway:.1f} months of reserves.')
        st.caption('The organization can focus on protecting unrestricted funding and monitoring staffing pressure.')

cols=st.columns(4)
cols[0].metric('Derived operating margin',f'{(revenue-expenses)/revenue:.1%}',border=True)
cols[1].metric('Derived cash runway',f'{runway:.1f} months',border=True)
cols[2].metric(f'Official {activity.lower()} jobs',f'{jobs:,.0f}',f'{job_change:+.1%} YoY',border=True)
cols[3].metric('Derived funding balance',gap_text,border=True)

summary_flow=pd.DataFrame({'Measure':['Revenue','Current expenses','Projected expenses','Cash reserves'],'Amount':[revenue,expenses,next_exp,cash],'Type':['Resource','Cost','Cost','Reserve']})
summary_latest=d[(d.GEO=='Canada')&(d.REF_DATE==d.REF_DATE.max())].copy()
summary_matrix=pd.DataFrame([{'Revenue change':r,'Expense growth':g,'Funding balance':revenue*(1+r)-expenses*(1+g)} for r in [-.1,-.05,0,.05,.1] for g in [0,.03,.06,.09,.12,.15]])
st.subheader('What the selected scenario shows')
top_left,top_right=st.columns(2)
with top_left.container(border=True):
    st.markdown('**Financial resource profile**')
    st.altair_chart(alt.Chart(summary_flow).mark_bar(cornerRadiusEnd=5).encode(x=alt.X('Amount:Q',title='Amount ($)'),y=alt.Y('Measure:N',sort=None,title=None),color=alt.Color('Type:N',scale=alt.Scale(domain=['Resource','Cost','Reserve'],range=['#153A47','#C65310','#29747A']),legend=None),tooltip=['Measure',alt.Tooltip('Amount',format='$,.0f')]),height=270)
    st.caption(f"Revenue covers {revenue/next_exp:.1%} of projected expenses. The projected balance is {gap_text}.")
with top_right.container(border=True):
    st.markdown(f'**Official {activity.lower()} employment trend**')
    st.altair_chart(alt.Chart(sector).mark_area(line={'color':'#153A47'},color='#D6E8E7').encode(x=alt.X('REF_DATE:O',title='Year'),y=alt.Y('VALUE:Q',title='Jobs (thousands)',scale=alt.Scale(zero=False)),tooltip=['REF_DATE','VALUE']),height=270)
    st.caption(f"Official {activity.lower()} employment is {jobs:,.0f}, a {job_change:+.1%} change from 2023.")
bottom_left,bottom_right=st.columns(2)
with bottom_left.container(border=True):
    st.markdown('**Funding stress matrix**')
    st.altair_chart(alt.Chart(summary_matrix).mark_rect(cornerRadius=3).encode(x=alt.X('Expense growth:O',axis=alt.Axis(format='%')),y=alt.Y('Revenue change:O',axis=alt.Axis(format='%')),color=alt.Color('Funding balance:Q',scale=alt.Scale(domainMid=0,range=['#A9470E','#FBF3EF','#29747A'])),tooltip=[alt.Tooltip('Funding balance',format='$,.0f')]),height=275)
    st.caption("Orange cells have a funding deficit. Teal cells have a surplus. Each cell uses the selected revenue and expense values.")
with bottom_right.container(border=True):
    st.markdown('**Latest nonprofit employment mix**')
    st.altair_chart(alt.Chart(summary_latest.nlargest(8,'VALUE')).mark_bar(cornerRadiusEnd=5).encode(x=alt.X('VALUE:Q',title='Jobs (thousands)'),y=alt.Y('Activity:N',sort='-x',title=None),color=alt.condition(f"datum.Activity == '{activity}'",alt.value('#C65310'),alt.value('#153A47')),tooltip=['Activity','VALUE']),height=275)
    st.caption(f"{summary_latest.loc[summary_latest.VALUE.idxmax(),'Activity']} is the largest activity at {summary_latest.VALUE.max()*1000:,.0f} jobs.")

health_tab, stress_tab, sector_tab, evidence_tab=st.tabs(['Financial health','Stress-test matrix','Sector labour market','Official evidence'])
with health_tab:
    left,right=st.columns([1.25,1])
    with left.container(border=True):
        st.subheader('Revenue coverage and reserves')
        flow=pd.DataFrame({'Measure':['Revenue','Current expenses','Projected expenses','Cash reserves'],'Amount':[revenue,expenses,next_exp,cash],'Type':['Resource','Cost','Cost','Reserve']})
        st.altair_chart(alt.Chart(flow).mark_bar(cornerRadiusEnd=5).encode(x=alt.X('Amount:Q',title='Amount ($)'),y=alt.Y('Measure:N',sort=None,title=None),color=alt.Color('Type:N',scale=alt.Scale(domain=['Resource','Cost','Reserve'],range=['#153A47','#C65310','#29747A']),legend=None),tooltip=['Measure',alt.Tooltip('Amount',format='$,.0f')]))
    with right.container(border=True):
        st.subheader('What is driving risk')
        risk=pd.DataFrame({'Factor':['Revenue coverage','Reserve runway','Expense growth'],'Score':[min(revenue/next_exp,1),min(runway/6,1),max(0,1-annual_growth/.15)]})
        weakest=risk.sort_values('Score').iloc[0]
        st.write(f'**Main weakness:** {weakest.Factor.lower()}. It is furthest from the planning threshold.')
        st.metric('Revenue coverage',f'{revenue/next_exp:.1%}')
        st.metric('Six-month reserve gap',f'${max(monthly_exp*6-cash,0):,.0f}')
        st.caption('Derived thresholds, not accounting standards or official ratings.')

with stress_tab:
    growth_rates=[0,.03,.06,.09,.12,.15]
    revenue_changes=[-.1,-.05,0,.05,.1]
    matrix=pd.DataFrame([{'Revenue change':r,'Expense growth':g,'Funding balance':revenue*(1+r)-expenses*(1+g)} for r in revenue_changes for g in growth_rates])
    heat=alt.Chart(matrix).mark_rect(cornerRadius=3).encode(x=alt.X('Expense growth:O',axis=alt.Axis(format='%')),y=alt.Y('Revenue change:O',axis=alt.Axis(format='%')),color=alt.Color('Funding balance:Q',scale=alt.Scale(domainMid=0,range=['#A9470E','#FBF3EF','#29747A'])),tooltip=[alt.Tooltip('Revenue change',format='.0%'),alt.Tooltip('Expense growth',format='.0%'),alt.Tooltip('Funding balance',format='$,.0f')])
    st.altair_chart(heat)
    st.caption('Each cell recalculates the next-year balance from the organization scenario.')

with sector_tab:
    left,right=st.columns([1.35,1])
    with left.container(border=True):
        st.subheader(f'Official employment trend in {activity.lower()}')
        chart=alt.Chart(sector).mark_area(line={'color':'#153A47'},color='#D6E8E7').encode(x=alt.X('REF_DATE:O',title='Year'),y=alt.Y('VALUE:Q',title='Jobs (thousands)',scale=alt.Scale(zero=False)),tooltip=['REF_DATE',alt.Tooltip('VALUE',format=',.0f')])
        st.altair_chart(chart)
    with right.container(border=True):
        latest_all=d[(d.GEO=='Canada')&(d.REF_DATE==d.REF_DATE.max())].copy()
        st.subheader('Latest employment mix')
        st.altair_chart(alt.Chart(latest_all.nlargest(8,'VALUE')).mark_bar(cornerRadiusEnd=5).encode(x=alt.X('VALUE:Q',title='Jobs (thousands)'),y=alt.Y('Activity:N',sort='-x',title=None),color=alt.condition(f"datum.Activity == '{activity}'",alt.value('#C65310'),alt.value('#153A47')),tooltip=['Activity','VALUE']))

with evidence_tab:
    official=d[d.GEO.eq('Canada')][['REF_DATE','Activity','VALUE','UOM','SCALAR_FACTOR']].copy(); official.columns=['Year','Official activity','Published value','Unit','Scale']
    st.dataframe(official,hide_index=True,key='nonprofit_evidence')

with st.expander('Method and sources',icon=':material/database:'):
    st.markdown('Sector employment: Statistics Canada table 36-10-0615-01, Employment in non-profit institutions by activity. Organization revenue, expense, cash, and growth values are user-controlled planning assumptions. The 2025 Ontario Nonprofit Network survey reported that 83% of respondents saw expenses increase, providing context for the stress test.')

