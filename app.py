from flask import Flask, render_template, request, jsonify
import matplotlib.pyplot as plt
import io
import base64
import json
import pickle
import joblib
import numpy as np

app = Flask(__name__)

AGE_BRACKETS = [
    "0-9", "10-19", "20-29", "30-39", "40-49",
    "50-59", "60-69", "70-79", "80-89", "90-99", "100+"
]

# Load the trained AI models (must be in the same directory)
birth_model = joblib.load("birth_model.pkl")
death_model = joblib.load("death_model.pkl")
migration_model = joblib.load("migration_model.pkl")

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


@app.route("/project_population", methods=["POST"])
def project_population():
    try:
        data = request.get_json()
        population = float(data.get("population", 0))
        gdp = float(data.get("gdp", 0))
        life = float(data.get("life", 0))
        urban = float(data.get("urban", 0))
        gdpScenario = data.get("gdpScenario", "medium")
        lifeScenario = data.get("lifeScenario", "medium")
        urbanScenario = data.get("urbanScenario", "medium")

        # Simple scenario multipliers (these should match your JS scenarioRates or adjust accordingly)
        scenario_growth = {
            "high": 0.02,
            "medium": 0.01,
            "low": 0.005,
            "stagnant": 0,
            "decline": -0.01
        }

        gdp_growth = scenario_growth.get(gdpScenario, 0.01)
        life_growth = scenario_growth.get(lifeScenario, 0.01)  # could be different scale
        urban_growth = scenario_growth.get(urbanScenario, 0.01)  # could be different scale

        years = list(range(2025, 2101, 5))
        populations = []
        current_pop = population

        for year in years:
            # For simplicity, just grow population by net growth rate influenced by GDP scenario
            # In real app, use AI prediction and scenario modifiers to get birth/death/migration
            net_growth_rate = gdp_growth - 0.005  # subtract small death rate estimate
            current_pop = current_pop * (1 + net_growth_rate * 5)  # 5-year steps
            populations.append(round(current_pop))

        return jsonify({"years": years, "population": populations})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
