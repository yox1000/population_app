import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

# Load dataset
df = pd.read_csv('demographics_multi_year.csv')

# Compute year-over-year percentage changes by country
df_pct = df.groupby('Country', group_keys=False).apply(
    lambda group: group.assign(
        GDP_per_capita=group['GDP_per_capita'].pct_change() * 100,
        Life_expectancy=group['Life_expectancy'].pct_change() * 100,
        Urbanization=group['Urbanization'].pct_change() * 100,
        Fertility_rate=group['Fertility_rate'].pct_change() * 100,
        Death_rate=group['Death_rate'].pct_change() * 100,
        Migration_rate=group['Migration_rate'].pct_change() * 100
    )
)

# Drop rows with NaN from pct_change
df_pct = df_pct.dropna()

# One-hot encode Region if present
if 'Region' in df_pct.columns:
    df_pct = pd.get_dummies(df_pct, columns=['Region'])

# Clean infinite and missing values
df_pct.replace([float('inf'), -float('inf')], pd.NA, inplace=True)
df_pct.dropna(subset=['Fertility_rate', 'Death_rate', 'Migration_rate'], inplace=True)

# Define input features
features = ['GDP_per_capita', 'Life_expectancy', 'Urbanization'] + \
           [col for col in df_pct.columns if col.startswith('Region_')]
X = df_pct[features]

# Define targets
y_birth = df_pct['Fertility_rate']
y_death = df_pct['Death_rate']
y_migration = df_pct['Migration_rate']

# Train models
birth_model = RandomForestRegressor(n_estimators=100, random_state=42)
death_model = RandomForestRegressor(n_estimators=100, random_state=42)
migration_model = RandomForestRegressor(n_estimators=100, random_state=42)

birth_model.fit(X, y_birth)
death_model.fit(X, y_death)
migration_model.fit(X, y_migration)

# Save models properly
joblib.dump(birth_model, 'birth_model.pkl')
joblib.dump(death_model, 'death_model.pkl')
joblib.dump(migration_model, 'migration_model.pkl')

print("Models trained and saved successfully.")
