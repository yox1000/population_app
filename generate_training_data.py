import pandas as pd
import numpy as np
import pycountry

# Get all recognized countries (196+)
countries = [country.name for country in pycountry.countries]

# Define development tiers with base values and trends
tiers = {
    "Developed": {
        "GDP": 50000,
        "Life": 80,
        "Urban": 80,
        "Fert": 1.6,
        "Death": 9.0,
        "Mig": 2.0,
        "GDP_growth": 0.02,
        "Life_increase": 0.3,
        "Urban_increase": 1.0,
        "Fertility_decline": 0.02,
        "Death_decline": 0.1,
        "Mig_variation": 0.5
    },
    "Emerging": {
        "GDP": 12000,
        "Life": 70,
        "Urban": 60,
        "Fert": 2.5,
        "Death": 7.0,
        "Mig": 0.0,
        "GDP_growth": 0.03,
        "Life_increase": 0.4,
        "Urban_increase": 1.5,
        "Fertility_decline": 0.01,
        "Death_decline": 0.05,
        "Mig_variation": 0.7
    },
    "LowIncome": {
        "GDP": 1500,
        "Life": 55,
        "Urban": 30,
        "Fert": 4.5,
        "Death": 12.0,
        "Mig": -0.2,
        "GDP_growth": 0.04,
        "Life_increase": 0.5,
        "Urban_increase": 2.0,
        "Fertility_decline": 0.0,
        "Death_decline": 0.0,
        "Mig_variation": 1.0
    }
}

# Simplified tier assignment based on some example countries
developed_countries = {
    "United States", "Germany", "Japan", "Canada", "France",
    "United Kingdom", "Australia", "Norway", "Sweden", "Switzerland",
    "Netherlands", "Denmark", "Finland", "Iceland", "Austria",
    "Belgium", "Ireland", "Luxembourg", "New Zealand", "Singapore"
}

emerging_countries = {
    "China", "India", "Brazil", "Mexico", "South Africa",
    "Indonesia", "Turkey", "Argentina", "Russia", "Saudi Arabia",
    "Thailand", "Malaysia", "Colombia", "Chile", "Peru",
    "Poland", "Czech Republic", "Hungary", "Romania", "Philippines"
}

def assign_tier(country_name):
    if country_name in developed_countries:
        return "Developed"
    elif country_name in emerging_countries:
        return "Emerging"
    else:
        return "LowIncome"

years = list(range(2000, 2040, 5))

records = []

np.random.seed(42)  # for reproducibility

for country in countries:
    tier = assign_tier(country)
    base = tiers[tier]
    for year in years:
        years_diff = year - 2025

        # Calculate values based on base and growth rates
        gdp = base["GDP"] * ((1 + base["GDP_growth"]) ** years_diff)
        life = base["Life"] + base["Life_increase"] * (years_diff / 5)
        urban = base["Urban"] + base["Urban_increase"] * (years_diff / 5)
        fert = base["Fert"] - base["Fertility_decline"] * (years_diff / 5)
        death = base["Death"] - base["Death_decline"] * (years_diff / 5)
        mig = base["Mig"] + np.random.uniform(-base["Mig_variation"], base["Mig_variation"]) * (years_diff / 5)

        # Clip values to reasonable ranges
        fert = max(fert, 0.5)
        death = max(death, 1)
        urban = min(max(urban, 10), 100)
        life = min(max(life, 40), 90)

        records.append({
            "Country": country,
            "Year": year,
            "GDP_per_capita": round(gdp, 2),
            "Life_expectancy": round(life, 2),
            "Urbanization": round(urban, 2),
            "Fertility_rate": round(fert, 2),
            "Death_rate": round(death, 2),
            "Migration_rate": round(mig, 2)
        })

df = pd.DataFrame(records)

df.to_csv("demographics_196_countries.csv", index=False)
print(f"Generated demographics_196_countries.csv with {len(df)} rows for {len(countries)} countries.")
