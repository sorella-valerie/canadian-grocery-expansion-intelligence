# Rellatech decision intelligence portfolio

Six separate Streamlit dashboards built from real public data. Run the complete local portfolio with:

```powershell
.\launch_all_dashboards.ps1
```

The local portfolio hub opens at `http://localhost:8509` and links to each independent dashboard.

See [DATA_GOVERNANCE.md](DATA_GOVERNANCE.md) for the official-source register, derived-measure definitions, vintages, and limitations.

A Streamlit portfolio dashboard for a fictional Canadian grocery operator deciding where to expand after balancing population growth, grocery demand, household purchasing power, and representative basket affordability.

## Run locally

```powershell
python -m streamlit run app.py
```

The seven prepared CSV files are bundled in `data/staging`, so the repository is self-contained and deployable on Streamlit Community Cloud.
