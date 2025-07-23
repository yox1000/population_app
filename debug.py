import joblib

birth_model = joblib.load("birth_model.pkl")
print(type(birth_model))
