import joblib
import numpy as np

birth_model = joblib.load('birth_model.pkl')
migration_model = joblib.load('migration_model.pkl')
death_model = joblib.load('death_model.pkl')
test_input = np.array([[1.5, 0.8, 2.0]])  # Example % changes
prediction = birth_model.predict(test_input)
print("Predicted birth rate change:", prediction)
