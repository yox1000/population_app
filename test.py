import joblib
import numpy as np

# Load models
birth_model = joblib.load('birth_model.pkl')
death_model = joblib.load('death_model.pkl')
migration_model = joblib.load('migration_model.pkl')

#Example
example = np.array([[67000, 81, 99]])  # GDP, Life expectancy, Urbanization

print("Birth rate:", round(birth_model.predict(example)[0], 2))
print("Death rate:", round(death_model.predict(example)[0], 2))
print("Migration rate:", round(migration_model.predict(example)[0], 2))
