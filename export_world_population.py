import pandas as pd

#convert data from kaggle dataset to the format needed for the model
#we create demo csv for test

# Load world population data
pop_df = pd.read_csv("world_population.csv")
pop_long = pop_df.melt(
    id_vars=["Country/Territory"],
    value_vars=["2020 Population", "2015 Population", "2010 Population", "2000 Population"],
    var_name="Year", value_name="Population"
)
pop_long["Year"] = pop_long["Year"].str.extract(r"(\d{4})").astype(int)
pop_long.rename(columns={"Country/Territory": "Country"}, inplace=True)

# Load birth rate data
birth_df = pd.read_csv("birth_rate_multiyear.csv")
birth_long = birth_df.melt(
    id_vars=["Country Name"],
    value_vars=[str(y) for y in [2000, 2005, 2010, 2015, 2020]],
    var_name="Year", value_name="Birth_rate"
)
birth_long["Year"] = birth_long["Year"].astype(int)
birth_long.rename(columns={"Country Name": "Country"}, inplace=True)

# Load demographics template
demo_df = pd.read_csv("demographics_multiyear_template.csv")

# Merge population
demo_df = demo_df.merge(
    pop_long,
    on=["Country", "Year"],
    how="left",
    suffixes=("", "_newpop")
)
valid_years = [2000, 2005, 2010, 2015, 2020]
mask_pop = demo_df["Year"].isin(valid_years) & demo_df["Population_newpop"].notna()
demo_df.loc[mask_pop, "Population"] = demo_df.loc[mask_pop, "Population_newpop"]
demo_df.drop(columns=["Population_newpop"], inplace=True)

# Merge birth rate
demo_df = demo_df.merge(
    birth_long,
    on=["Country", "Year"],
    how="left",
    suffixes=("", "_newbirth")
)
mask_birth = demo_df["Year"].isin(valid_years) & demo_df["Birth_rate_newbirth"].notna()
demo_df.loc[mask_birth, "Birth_rate"] = demo_df.loc[mask_birth, "Birth_rate_newbirth"]
demo_df.drop(columns=["Birth_rate_newbirth"], inplace=True)

# Save final file
demo_df.to_csv("demographics_multiyear.csv", index=False, encoding="utf-8")
print("demographics_multiyear.csv exported successfully")
