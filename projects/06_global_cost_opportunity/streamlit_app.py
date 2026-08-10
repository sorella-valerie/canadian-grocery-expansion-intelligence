from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st

ROOT=Path(__file__).parent
@st.cache_data
def load(): return pd.read_csv(ROOT/'data/world_bank_country_profiles.csv')
def norm(s,higher=True):
    z=(s-s.min())/(s.max()-s.min()) if s.max()>s.min() else pd.Series(.5,index=s.index)
    return z if higher else 1-z

st.set_page_config(page_title='Global cost and opportunity explorer',page_icon=':material/public:',layout='wide')
d=load()
with st.sidebar:
    st.title('Relocation priorities')
    home=st.selectbox('Country to inspect',sorted(d.country),index=sorted(d.country).index('Canada'))
    priority=st.selectbox('Primary goal',['Balanced opportunity','Higher purchasing power','Lower unemployment','Lower inflation','Stronger health investment'])
    shortlist=st.multiselect('Countries to compare',sorted(d.country),default=sorted(d.country))

d=d[d.country.isin(shortlist)].copy()
if len(d)<2:
    st.warning('Select at least two countries for a meaningful comparison.',icon=':material/public:')
    st.stop()
weights={'Balanced opportunity':(.35,.25,.2,.2),'Higher purchasing power':(.6,.15,.15,.1),'Lower unemployment':(.2,.6,.1,.1),'Lower inflation':(.2,.15,.55,.1),'Stronger health investment':(.2,.15,.1,.55)}[priority]
d['score']=(norm(d.income_ppp)*weights[0]+norm(d.unemployment,False)*weights[1]+norm(d.inflation,False)*weights[2]+norm(d.health_spend_pc)*weights[3])*100
d=d.sort_values('score',ascending=False).reset_index(drop=True); d['rank']=d.index+1
best=d.iloc[0]; chosen=d[d.country.eq(home)].iloc[0] if home in d.country.values else best

st.title('Global cost-of-living & opportunity explorer')
st.write('Compare purchasing power, unemployment, inflation, and health spending across selected countries.')
st.caption('Official World Bank indicators use the latest country observation from 2021 to 2025. The ranking is derived and is not a city cost-of-living estimate.')
with st.container(border=True):
    if chosen.country==best.country:
        st.subheader(f'{chosen.country} ranks first for {priority.lower()}, scoring {chosen.score:.0f}/100.')
    else:
        st.subheader(f'{chosen.country} ranks {int(chosen["rank"])} of {len(d)}. {best.country} ranks first for {priority.lower()}.')
    pressure='inflation' if chosen.inflation>d.inflation.median() else 'unemployment' if chosen.unemployment>d.unemployment.median() else 'relative purchasing power'
    st.caption(f'The main screening concern for {chosen.country} is {pressure}. Validate taxes, visas, rent, and city-level costs before making a decision.')

cols=st.columns(4)
cols[0].metric('Official PPP income per person',f'${chosen.income_ppp:,.0f}',border=True)
cols[1].metric('Official unemployment',f'{chosen.unemployment:.1f}%',border=True)
cols[2].metric('Official inflation',f'{chosen.inflation:.1f}%',border=True)
cols[3].metric('Official health spend per person',f'${chosen.health_spend_pc:,.0f}',border=True)

summary_metrics=pd.DataFrame({'country':d.country,'Purchasing power':norm(d.income_ppp)*100,'Employment':norm(d.unemployment,False)*100,'Price stability':norm(d.inflation,False)*100,'Health investment':norm(d.health_spend_pc)*100})
summary_long=summary_metrics.melt('country',var_name='Dimension',value_name='Position')
st.subheader('What the selected indicators show')
top_left,top_right=st.columns(2)
with top_left.container(border=True):
    st.markdown('**Purchasing power and employment frontier**')
    st.altair_chart(alt.Chart(d).mark_circle(opacity=.85).encode(x=alt.X('unemployment:Q',title='Unemployment (%)'),y=alt.Y('income_ppp:Q',title='PPP income ($)',scale=alt.Scale(zero=False)),size=alt.Size('health_spend_pc:Q',legend=None,scale=alt.Scale(range=[100,750])),color=alt.condition(f"datum.country == '{chosen.country}'",alt.value('#C65310'),alt.value('#153A47')),tooltip=['country','unemployment','income_ppp']),height=280)
    st.caption(f"{chosen.country} has ${chosen.income_ppp:,.0f} PPP income per person and {chosen.unemployment:.1f}% unemployment.")
with top_right.container(border=True):
    st.markdown('**Scenario ranking**')
    st.altair_chart(alt.Chart(d.head(15)).mark_bar(cornerRadiusEnd=5).encode(x=alt.X('score:Q',title='Scenario score',scale=alt.Scale(domain=[0,100])),y=alt.Y('country:N',sort='-x',title=None),color=alt.condition(f"datum.country == '{chosen.country}'",alt.value('#C65310'),alt.value('#153A47')),tooltip=['country','score']),height=280)
    st.caption(f"{chosen.country} scores {chosen.score:.0f}. {best.country} leads by {best.score-chosen.score:.0f} points.")
bottom_left,bottom_right=st.columns(2)
with bottom_left.container(border=True):
    st.markdown('**Country indicator fingerprint**')
    st.altair_chart(alt.Chart(summary_long).mark_rect(cornerRadius=3).encode(x=alt.X('Dimension:N',title=None),y=alt.Y('country:N',sort=d.country.tolist(),title=None),color=alt.Color('Position:Q',scale=alt.Scale(range=['#FBF3EF','#153A47'])),tooltip=['country','Dimension','Position']),height=285)
    st.caption("Darker cells show a higher normalized position within the selected countries. These positions are derived.")
with bottom_right.container(border=True):
    st.markdown('**Inflation and unemployment pressure**')
    st.altair_chart(alt.Chart(d).mark_circle(size=160).encode(x=alt.X('inflation:Q',title='Inflation (%)'),y=alt.Y('unemployment:Q',title='Unemployment (%)'),color=alt.condition(f"datum.country == '{chosen.country}'",alt.value('#C65310'),alt.value('#153A47')),tooltip=['country','inflation','unemployment']),height=285)
    st.caption(f"{chosen.country} has {chosen.inflation:.1f}% inflation and {chosen.unemployment:.1f}% unemployment. Lower values indicate less current pressure.")

frontier_tab, fingerprint_tab, rank_tab, evidence_tab=st.tabs(['Opportunity frontier','Country fingerprint','Scenario ranking','Official evidence'])
with frontier_tab:
    st.subheader('Purchasing power versus labour-market pressure')
    st.caption('Upper left is stronger: higher PPP income and lower unemployment. Bubble size represents official health expenditure per person.')
    chart=alt.Chart(d).mark_circle(opacity=.85).encode(x=alt.X('unemployment:Q',title='Official unemployment rate (%)'),y=alt.Y('income_ppp:Q',title='Official GDP per capita, PPP ($)',scale=alt.Scale(zero=False)),size=alt.Size('health_spend_pc:Q',title='Health spending',scale=alt.Scale(range=[100,1000])),color=alt.condition(f"datum.country == '{chosen.country}'",alt.value('#C65310'),alt.value('#153A47')),tooltip=['country',alt.Tooltip('income_ppp',format='$,.0f'),alt.Tooltip('unemployment',format='.1f'),alt.Tooltip('inflation',format='.1f'),alt.Tooltip('health_spend_pc',format='$,.0f')])
    st.altair_chart(chart)

with fingerprint_tab:
    metrics=pd.DataFrame({'country':d.country,'Purchasing power':norm(d.income_ppp)*100,'Employment':norm(d.unemployment,False)*100,'Price stability':norm(d.inflation,False)*100,'Health investment':norm(d.health_spend_pc)*100})
    long=metrics.melt('country',var_name='Dimension',value_name='Normalized position')
    heat=alt.Chart(long).mark_rect(cornerRadius=3).encode(x=alt.X('Dimension:N',title=None),y=alt.Y('country:N',sort=d.country.tolist(),title=None),color=alt.Color('Normalized position:Q',scale=alt.Scale(range=['#FBF3EF','#153A47'])),tooltip=['country','Dimension',alt.Tooltip('Normalized position',format='.0f')])
    st.altair_chart(heat)
    st.caption('Derived min-max positions within the selected countries. These are not official ratings.')

with rank_tab:
    left,right=st.columns([1.25,1])
    with left.container(border=True):
        bars=alt.Chart(d.head(15)).mark_bar(cornerRadiusEnd=5).encode(x=alt.X('score:Q',scale=alt.Scale(domain=[0,100]),title='Derived scenario score'),y=alt.Y('country:N',sort='-x',title=None),color=alt.condition(f"datum.country == '{chosen.country}'",alt.value('#C65310'),alt.value('#153A47')),tooltip=['country',alt.Tooltip('score',format='.0f')])
        st.altair_chart(bars)
    with right.container(border=True):
        st.subheader('Why the result changes')
        st.write(f'Active priority: **{priority}**')
        st.write(f'Weights: purchasing power {weights[0]:.0%}, employment {weights[1]:.0%}, price stability {weights[2]:.0%}, health investment {weights[3]:.0%}.')
        st.metric('Gap to leader',f'{best.score-chosen.score:.0f} points')
        st.caption('Change the primary goal to recalculate every rank and narrative.')

with evidence_tab:
    show=d[['rank','country','income_ppp','income_ppp_year','unemployment','unemployment_year','inflation','inflation_year','health_spend_pc','health_spend_pc_year','score']].copy()
    show.columns=['Scenario rank','Country','Official PPP income','Income year','Official unemployment','Unemployment year','Official inflation','Inflation year','Official health spend','Health year','Scenario score']
    st.dataframe(show,hide_index=True,key='global_evidence',column_config={'Official PPP income':st.column_config.NumberColumn(format='$%.0f'),'Official unemployment':st.column_config.NumberColumn(format='%.1f%%'),'Official inflation':st.column_config.NumberColumn(format='%.1f%%'),'Official health spend':st.column_config.NumberColumn(format='$%.0f'),'Scenario score':st.column_config.ProgressColumn(min_value=0,max_value=100,format='%.0f')})

with st.expander('Method and source',icon=':material/database:'):
    st.markdown('Source: World Bank Indicators API. Purchasing power uses GDP per capita in current international dollars. Cost pressure uses consumer-price inflation, which measures change rather than the absolute price level. The score is a transparent portfolio scenario, not an official World Bank indicator.')

