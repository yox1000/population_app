import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib

#Load dataset
df = pd.read_csv('demographics.csv')

# Input features
features = ['GDP_per_capita', 'Life_expectancy', 'Urbanization']
X = df[features]

# Targets 
y_birth = df['Fertility_rate']
y_death = df['Death_rate']
y_migration = df['Migration_rate']

# Step 3: Train models
birth_model = RandomForestRegressor(n_estimators=100, random_state=42)
death_model = RandomForestRegressor(n_estimators=100, random_state=42)
migration_model = RandomForestRegressor(n_estimators=100, random_state=42)

birth_model.fit(X, y_birth)
death_model.fit(X, y_death)
migration_model.fit(X, y_migration)

# Step 4: Save models 
joblib.dump(birth_model, 'birth_model.pkl')
joblib.dump(death_model, 'death_model.pkl')
joblib.dump(migration_model, 'migration_model.pkl')

print("Models trained and saved.")
