from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

CITIES = {
    "Vancouver": ("Vancouver, British Columbia", "BC", "British Columbia", 49.2827, -123.1207),
    "Calgary": ("Calgary, Alberta", "AB", "Alberta", 51.0447, -114.0719),
    "Edmonton": ("Edmonton, Alberta", "AB", "Alberta", 53.5461, -113.4938),
    "Saskatoon": ("Saskatoon, Saskatchewan", "SK", "Saskatchewan", 52.1579, -106.6702),
    "Winnipeg": ("Winnipeg, Manitoba", "MB", "Manitoba", 49.8954, -97.1385),
    "Toronto": ("Toronto, Ontario", "ON", "Ontario", 43.6532, -79.3832),
    "Ottawa": ("Ottawa-Gatineau, Ontario/Quebec", "ON", "Ontario", 45.4215, -75.6972),
    "Montreal": ("MontrÃ©al, Quebec", "QC", "Quebec", 45.5019, -73.5674),
    "Halifax": ("Halifax, Nova Scotia", "NS", "Nova Scotia", 44.6488, -63.5752),
    "Moncton": ("Moncton, New Brunswick", "NB", "New Brunswick", 46.0878, -64.7782),
}

OCCUPATIONS = {
    "Software developer": "NOC_21232",
    "Data analyst": "NOC_21223",
    "Registered nurse": "NOC_31301",
    "Customer service representative": "NOC_64400",
    "Accountant": "NOC_11100",
    "Secondary school teacher": "NOC_41220",
    "Electrician": "NOC_72200",
    "Administrative assistant": "NOC_13110",
    "Transport truck driver": "NOC_73300",
    "Retail salesperson": "NOC_64100",
}


def normalize(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    lo, hi = series.min(), series.max()
    result = (series - lo) / (hi - lo) if hi > lo else pd.Series(0.5, index=series.index)
    return result if higher_is_better else 1 - result


def build_city_profiles() -> pd.DataFrame:
    rent = pd.read_csv(RAW / "rent" / "34100133.csv", low_memory=False)
    rent = rent[(rent["REF_DATE"] == rent["REF_DATE"].max()) &
                (rent["Type of structure"] == "Row and apartment structures of three units and over") &
                (rent["Type of unit"].isin(["One bedroom units", "Two bedroom units"]))]
    rows = []
    for city, (geo, code, province, lat, lon) in CITIES.items():
        match = rent[rent["GEO"].str.startswith("Montr" if city == "Montreal" else city, na=False)]
        values = dict(zip(match["Type of unit"], match["VALUE"]))
        rows.append({"city": city, "province_code": code, "province": province, "latitude": lat,
                     "longitude": lon, "rent_1br": values.get("One bedroom units"),
                     "rent_2br": values.get("Two bedroom units")})
    return pd.DataFrame(rows)


def build_wages() -> pd.DataFrame:
    wages = pd.read_csv(RAW / "jobbank_wages_2025.csv", low_memory=False)
    rows = []
    for occupation, noc in OCCUPATIONS.items():
        subset = wages[wages["NOC_CNP"] == noc]
        for city, (_, code, province, _, _) in CITIES.items():
            candidates = subset[subset["prov"] == code]
            hourly = pd.to_numeric(candidates["Median_Wage_Salaire_Median"], errors="coerce").median()
            annual_flag = candidates["Annual_Wage_Flag_Salaire_annuel"].astype(str).str.lower().eq("true").any()
            annual = hourly if annual_flag else hourly * 2080
            rows.append({"city": city, "occupation": occupation, "noc": noc.replace("NOC_", ""),
                         "median_annual_wage": round(float(annual), 0) if pd.notna(annual) else np.nan})
    return pd.DataFrame(rows)


def build_baskets() -> pd.DataFrame:
    food = pd.read_csv(RAW / "FactFoodPrices.csv")
    products = pd.read_csv(RAW / "DimProduct.csv")
    latest = food[food["Date"] == food["Date"].max()].merge(products, on="Product")
    latest["weighted"] = latest["Price"] * latest["BasketWeight"]
    result = latest.groupby("Geography", as_index=False)["weighted"].sum()
    result["monthly_food_per_person"] = result["weighted"] * 52 / 12
    return result.rename(columns={"Geography": "province"})[["province", "monthly_food_per_person"]]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    city = build_city_profiles().merge(build_baskets(), on="province", how="left")
    city.to_csv(OUT / "city_profiles.csv", index=False)
    build_wages().to_csv(OUT / "occupation_wages.csv", index=False)


main()

