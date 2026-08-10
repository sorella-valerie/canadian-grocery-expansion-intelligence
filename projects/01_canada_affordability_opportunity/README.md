# Canada affordability & opportunity explorer

A standalone Streamlit decision dashboard that compares ten Canadian cities for a selected occupation, salary, household size, bedroom count and transportation choice.

## Run locally

```powershell
python data_pipeline.py
python -m streamlit run streamlit_app.py
```

## Real data sources

- [Statistics Canada table 34-10-0133-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410013301): average rents by metropolitan area
- [Government of Canada Job Bank wage data](https://open.canada.ca/data/en/dataset/adad580f-76b0-4502-bd05-20c125de9116)
- [Government of Canada Job Bank outlook data](https://open.canada.ca/data/en/dataset/b0e112e9-cf53-4e79-8838-23cd98debe5b)
- [Statistics Canada table 18-10-0245-02](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810024502): monthly average retail food prices
- [CRA 2026 income tax rates](https://www.canada.ca/en/revenue-agency/services/tax/individuals/frequently-asked-questions-individuals/adjustment-personal-income-tax-benefit-amounts.html)

The result is a planning scenario, not a tax calculation or official government indicator.
