from flask import Flask, render_template, request, jsonify
import matplotlib.pyplot as plt
import io
import base64
import json
import pickle
import joblib
import numpy as np
import logging
from datetime import datetime
import os

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AGE_BRACKETS = [
    "0-9", "10-19", "20-29", "30-39", "40-49",
    "50-59", "60-69", "70-79", "80-89", "90-99", "100+"
]

# Load demographics data from JSON file for filling in frontend
def load_demographics_data():
    try:
        with open('demographics.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("demographics.json file not found")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing demographics.json: {e}")
        return {}

DEMOGRAPHICS_DATA = load_demographics_data()

# Load the trained AI models with error handling
try:
    birth_model = joblib.load("birth_model.pkl")
    death_model = joblib.load("death_model.pkl")
    migration_model = joblib.load("migration_model.pkl")
    logger.info("AI models loaded successfully")
except FileNotFoundError as e:
    logger.error(f"Model file not found: {e}")
    birth_model = death_model = migration_model = None
except Exception as e:
    logger.error(f"Error loading models: {e}")
    birth_model = death_model = migration_model = None

@app.route("/")
def index():
    return render_template("index.html", age_brackets=AGE_BRACKETS)

@app.route("/get-country-data/<country>")
def get_country_data(country):
    """Gets demographic data for a specified country"""
    try:
        country_lower = country.lower()
        if country_lower not in DEMOGRAPHICS_DATA:
            return jsonify({"error": f"Country '{country}' not found"}), 404
        
        data = DEMOGRAPHICS_DATA[country_lower]
        return jsonify({
            #fallback included as second value in data.get ()
            "population": data.get("population", 0),
            "male_pyramid_data": data.get("male_pyramid_data", [0] * 11),
            "female_pyramid_data": data.get("female_pyramid_data", [0] * 11),
            "gdp_per_capita": data.get("gdp_per_capita", 0),
            "life_expectancy": data.get("life_expectancy", 70),
            "urbanization": data.get("urbanization", 0)
        })
        
    except Exception as e:
        logger.error(f"Error getting country data: {e}")
        return jsonify({"error": "Failed to retrieve country data"}), 500

@app.route("/generate-chart", methods=["POST"])
def generate_chart():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        males = [-float(x) for x in data.get("male", [0]*len(AGE_BRACKETS))]
        females = [float(x) for x in data.get("female", [0]*len(AGE_BRACKETS))]

        # Validate data lengths
        if len(males) != len(AGE_BRACKETS) or len(females) != len(AGE_BRACKETS):
            return jsonify({"error": "Invalid data length"}), 400

        # Create the chart with improved styling
        fig, ax = plt.subplots(figsize=(10, 8))
        y_pos = list(range(len(AGE_BRACKETS)))

        # Create horizontal bar chart
        bars_male = ax.barh(y_pos, males, color='#2196F3', label='Male', alpha=0.8)
        bars_female = ax.barh(y_pos, females, color='#E91E63', label='Female', alpha=0.8)

        # Customize the chart
        ax.set_yticks(y_pos)
        ax.set_yticklabels(AGE_BRACKETS)
        ax.set_xlabel('Population %', fontsize=12, fontweight='bold')
        ax.set_title('Population Pyramid', fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='upper right')
        ax.grid(axis='x', linestyle='--', alpha=0.7)
        ax.axvline(x=0, color='black', linewidth=0.8)

        # Add percentage labels on bars
        for i, (m, f) in enumerate(zip(males, females)):
            if abs(m) > 0.5:  # Only show label if bar is significant
                ax.text(m/2, i, f'{abs(m):.1f}%', ha='center', va='center', 
                       fontsize=8, color='white', fontweight='bold')
            if f > 0.5:
                ax.text(f/2, i, f'{f:.1f}%', ha='center', va='center', 
                       fontsize=8, color='white', fontweight='bold')

        # Improve layout
        plt.tight_layout()

        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()

        return jsonify({"chart": chart_base64})
        
    except ValueError as e:
        logger.error(f"Value error in generate_chart: {e}")
        return jsonify({"error": "Invalid numeric values provided"}), 400
    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        return jsonify({"error": "Failed to generate chart"}), 500

@app.route("/predict", methods=["POST"])
def predict():
    try:
        if not all([birth_model, death_model, migration_model]):
            return jsonify({"error": "AI models not available"}), 503
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Validate input parameters
        required_fields = ["gdp", "life", "urban"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
                
        gdp = float(data["gdp"])
        life = float(data["life"])
        urban = float(data["urban"])
        
        # Validate ranges
        if gdp < 0 or life < 0 or life > 120 or urban < 0 or urban > 100:
            return jsonify({"error": "Invalid parameter ranges"}), 400
        
        # Prepare features for prediction
        features = np.array([[gdp, life, urban]])

        # Make predictions
        birth = float(birth_model.predict(features)[0])
        death = float(death_model.predict(features)[0])
        migration = float(migration_model.predict(features)[0])
        
        # Ensure reasonable bounds
        birth = max(0, min(birth, 50))  # Birth rate between 0-50 per 1000
        death = max(0, min(death, 50))  # Death rate between 0-50 per 1000
        migration = max(-20, min(migration, 20))  # Migration rate between -20 to 20 per 1000

        return jsonify({
            "birthRate": round(birth, 2),
            "deathRate": round(death, 2),
            "migrationRate": round(migration, 2)
        })
        
    except ValueError as e:
        logger.error(f"Value error in predict: {e}")
        return jsonify({"error": "Invalid numeric values provided"}), 400
    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        return jsonify({"error": "Prediction failed"}), 500

@app.route("/project_population", methods=["POST"])
def project_population():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        population = float(data.get("population", 0))
        gdp = float(data.get("gdp", 0))
        life = float(data.get("life", 0))
        urban = float(data.get("urban", 0))
        
        if population <= 0:
            return jsonify({"error": "Invalid population value"}), 400
        
        gdpScenario = data.get("gdpScenario", "medium")
        lifeScenario = data.get("lifeScenario", "medium")
        urbanScenario = data.get("urbanScenario", "medium")

        # Enhanced scenario multipliers with more realistic projections
        scenario_multipliers = {
            "high": {"gdp": 0.03, "life": 0.4, "urban": 1.0},
            "medium": {"gdp": 0.015, "life": 0.2, "urban": 0.5},
            "low": {"gdp": 0.005, "life": 0.1, "urban": 0.2},
            "stagnant": {"gdp": 0, "life": 0, "urban": 0},
            "decline": {"gdp": -0.015, "life": -0.1, "urban": -0.3}
        }

        gdp_mult = scenario_multipliers.get(gdpScenario, scenario_multipliers["medium"])["gdp"]
        life_mult = scenario_multipliers.get(lifeScenario, scenario_multipliers["medium"])["life"]
        urban_mult = scenario_multipliers.get(urbanScenario, scenario_multipliers["medium"])["urban"]

        years = list(range(2025, 2101, 5))
        populations = []
        current_pop = population
        current_gdp = gdp
        current_life = life
        current_urban = urban

        for i, year in enumerate(years):
            if i > 0:  # Don't modify the base year
                # Apply scenario growth to indicators
                current_gdp *= (1 + gdp_mult)
                current_life += life_mult
                current_urban = min(100, max(0, current_urban + urban_mult))
                
                # If AI models are available, use them for more accurate predictions
                if all([birth_model, death_model, migration_model]):
                    try:
                        features = np.array([[current_gdp, current_life, current_urban]])
                        birth_rate = float(birth_model.predict(features)[0]) / 1000  # Convert to rate
                        death_rate = float(death_model.predict(features)[0]) / 1000
                        migration_rate = float(migration_model.predict(features)[0]) / 1000
                        
                        net_growth_rate = birth_rate - death_rate + migration_rate
                    except Exception as e:
                        logger.warning(f"AI prediction failed, using fallback: {e}")
                        net_growth_rate = gdp_mult - 0.008  # Fallback calculation
                else:
                    # Fallback calculation based on GDP scenario
                    net_growth_rate = gdp_mult - 0.008
                
                # Apply demographic transition effects
                # Higher GDP typically leads to lower birth rates
                if current_gdp > 20000:
                    net_growth_rate *= 0.7
                elif current_gdp > 50000:
                    net_growth_rate *= 0.5
                
                # Calculate population for next period (5-year projection)
                current_pop = current_pop * (1 + net_growth_rate * 5)
                
                # Ensure population doesn't go negative
                current_pop = max(current_pop, 1000)
            
            populations.append(round(current_pop))

        return jsonify({
            "years": years, 
            "population": populations,
            "metadata": {
                "scenarios": {
                    "gdp": gdpScenario,
                    "life": lifeScenario,
                    "urban": urbanScenario
                },
                "final_indicators": {
                    "gdp": round(current_gdp, 2),
                    "life": round(current_life, 1),
                    "urban": round(current_urban, 1)
                }
            }
        })

    except ValueError as e:
        logger.error(f"Value error in project_population: {e}")
        return jsonify({"error": "Invalid numeric values provided"}), 400
    except Exception as e:
        logger.error(f"Error in population projection: {e}")
        return jsonify({"error": "Population projection failed"}), 500

@app.route("/health")
def health_check():
    """Health check endpoint"""
    models_status = {
        "birth_model": birth_model is not None,
        "death_model": death_model is not None,
        "migration_model": migration_model is not None
    }
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "models": models_status
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)