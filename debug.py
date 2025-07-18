import pickle
with open("birth_model.pkl", "rb") as f:
    birth_model = pickle.load(f)
print(type(birth_model))
