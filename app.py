from flask import Flask, render_template, request, jsonify
import matplotlib.pyplot as plt
import io
import base64
import json
import pickle
import numpy as np

app = Flask(__name__)

AGE_BRACKETS = [
    "0-9", "10-19", "20-29", "30-39", "40-49",
    "50-59", "60-69", "70-79", "80-89", "90-99", "100+"
]

# Load the trained AI models (must be in the same directory)
with open("birth_model.pkl", "rb") as f:
    birth_model = pickle.load(f)

with open("death_model.pkl", "rb") as f:
    death_model = pickle.load(f)

with open("migration_model.pkl", "rb") as f:
    migration_model = pickle.load(f)

@app.route("/")
def index():
    return render_template("index.html", age_brackets=AGE_BRACKETS)

@app.route("/generate-chart", methods=["POST"])
def generate_chart():
    try:
        data = request.json
        males = [-float(x) for x in data.get("male", [0]*len(AGE_BRACKETS))]
        females = [float(x) for x in data.get("female", [0]*len(AGE_BRACKETS))]

        fig, ax = plt.subplots(figsize=(8, 6))
        y_pos = list(range(len(AGE_BRACKETS)))

        ax.barh(y_pos, males, color='blue', label='Male')
        ax.barh(y_pos, females, color='pink', label='Female')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(AGE_BRACKETS)
        ax.set_xlabel('Population %')
        ax.set_title('Population Pyramid')
        ax.legend()
        ax.grid(axis='x', linestyle='--', alpha=0.7)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()

        return jsonify({"chart": chart_base64})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        gdp = float(data["gdp"])
        life = float(data["life"])
        urban = float(data["urban"])
        features = np.array([[gdp, life, urban]])

        birth = float(birth_model.predict(features)[0])
        death = float(death_model.predict(features)[0])
        migration = float(migration_model.predict(features)[0])

        return jsonify({
            "birthRate": round(birth, 2),
            "deathRate": round(death, 2),
            "migrationRate": round(migration, 2)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
