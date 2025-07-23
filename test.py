import joblib
import pandas as pd

# Load model
birth_model = joblib.load("birth_model.pkl")

# load training data if I want to test on it
df = pd.read_csv("demographics_multi_year.csv")
df_pct = df.groupby('Country', group_keys=False).apply(
    lambda group: group.assign(
        GDP_per_capita=group['GDP_per_capita'].pct_change() * 100,
        Life_expectancy=group['Life_expectancy'].pct_change() * 100,
        Urbanization=group['Urbanization'].pct_change() * 100,
        Fertility_rate=group['Fertility_rate'].pct_change() * 100,
        Death_rate=group['Death_rate'].pct_change() * 100,
        Migration_rate=group['Migration_rate'].pct_change() * 100
    )
).dropna()

if 'Region' in df_pct.columns:
    df_pct = pd.get_dummies(df_pct, columns=['Region'])

features = ['GDP_per_capita', 'Life_expectancy', 'Urbanization'] + \
           [col for col in df_pct.columns if col.startswith('Region_')]
X = df_pct[features]
y = df_pct['Fertility_rate']

# Evaluate model
print("Model type:", type(birth_model))
print("R^2 score on training data:", birth_model.score(X, y))
print("Feature importances:", birth_model.feature_importances_)
