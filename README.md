# Rellatech Decision Intelligence Portfolio

Six interactive Streamlit dashboards that turn official public data and clearly labelled planning scenarios into practical decisions.

## [Explore the complete live portfolio](https://rellatech-decision-intelligence.streamlit.app/)

| Dashboard | Question answered | Live app |
|---|---|---|
| Canadian grocery expansion intelligence | Which provinces offer the strongest mix of growth, demand, income and affordability? | [Open](https://canadian-grocery-expansion-intelligence.streamlit.app/) |
| Canada affordability and opportunity | Where can a household balance local wages, rent and essential costs? | [Open](https://canada-affordability-opportunity.streamlit.app/) |
| Canadian healthcare access | Where are mapped healthcare facilities concentrated or limited? | [Open](https://canadian-healthcare-access.streamlit.app/) |
| Newcomer settlement navigator | Which Canadian cities best match a household and occupation scenario? | [Open](https://canada-newcomer-settlement.streamlit.app/) |
| Canadian food affordability | Which products and provinces are driving grocery pressure? | [Open](https://canada-food-affordability.streamlit.app/) |
| Nonprofit sustainability | How do revenue, expenses and reserves affect financial runway? | [Open](https://nonprofit-sustainability.streamlit.app/) |
| Global cost and opportunity | Which countries align with a selected relocation priority? | [Open](https://global-cost-opportunity.streamlit.app/) |

## What this portfolio demonstrates

- Data cleaning, validation and reproducible transformations
- Interactive decision flows and plain-language analytical narratives
- Scenario modelling with transparent assumptions
- Geographic, financial and operational analysis
- Responsive dashboard design using Streamlit, Python, Pandas and Altair
- Clear separation of official published values from derived planning measures

## Evidence standard

Official published values are never presented as locally calculated scores. Each dashboard identifies its data vintage, source limitations and derived assumptions. See [DATA_GOVERNANCE.md](DATA_GOVERNANCE.md) for the complete source register and methodology notes.

## Run locally

Install the root requirements and launch all apps:

```powershell
pip install -r requirements.txt
.\launch_all_dashboards.ps1
```

The portfolio hub opens at `http://localhost:8509`. Each project also has its own requirements file and README.

## Services

Rellatech helps small businesses, nonprofits and growing teams with data analysis, dashboards, automation, CRM workflows and digital operations. Visit [Rellatech.io](https://rellatech.io).
