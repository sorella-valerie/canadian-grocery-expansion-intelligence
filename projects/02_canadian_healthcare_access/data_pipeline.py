from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
raw = pd.read_csv(ROOT / "data/raw/odhf_bdoes_v1.csv", encoding="cp1252", low_memory=False)
raw["province"] = raw["province"].str.upper()
raw["city"] = raw["city"].fillna(raw["CSDname"]).str.title()
raw["facility_type"] = raw["odhf_facility_type"].replace({
    "Ambulatory health care services": "Clinics and ambulatory care",
    "Nursing and residential care facilities": "Residential and long-term care",
})
raw.loc[raw["facility_type"].str.lower().eq("nursing and residential care facilities"), "facility_type"] = "Residential and long-term care"
clean = raw[["facility_name", "facility_type", "city", "province", "latitude", "longitude", "provider"]].copy()
clean = clean.dropna(subset=["latitude", "longitude"])
clean = clean[clean["latitude"].between(41, 84) & clean["longitude"].between(-142, -52)]
out = ROOT / "data/processed"
out.mkdir(parents=True, exist_ok=True)
clean.to_csv(out / "facilities.csv", index=False)

