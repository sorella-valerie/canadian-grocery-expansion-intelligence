from pathlib import Path
import requests
import pandas as pd

ROOT=Path(__file__).parent; OUT=ROOT/'data'; OUT.mkdir(exist_ok=True)
COUNTRIES=['CAN','USA','GBR','IRL','DEU','FRA','NLD','PRT','ESP','AUS','NZL','JPN','KOR','SGP','ARE','MEX','CRI','CHL','POL','CZE']
INDICATORS={'income_ppp':'NY.GDP.PCAP.PP.CD','unemployment':'SL.UEM.TOTL.ZS','inflation':'FP.CPI.TOTL.ZG','health_spend_pc':'SH.XPD.CHEX.PC.CD','urban_share':'SP.URB.TOTL.IN.ZS'}
rows={}
for label,indicator in INDICATORS.items():
    url=f'https://api.worldbank.org/v2/country/{";".join(COUNTRIES)}/indicator/{indicator}?format=json&per_page=2000&date=2021:2025'
    data=requests.get(url,timeout=30).json()[1]
    for item in data:
        if item['value'] is None: continue
        code=item['countryiso3code']; key=(code,item['country']['value'])
        current=rows.setdefault(key,{})
        if label not in current: current[label]=item['value']; current[label+'_year']=item['date']
records=[]
for (code,country),values in rows.items():
    if all(k in values for k in INDICATORS): records.append({'code':code,'country':country,**values})
pd.DataFrame(records).to_csv(OUT/'world_bank_country_profiles.csv',index=False)


