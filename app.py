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
import pandas as pd

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
            "population": data.get("population", 0),
            "male_pyramid_data": data.get("male_pyramid_data", [0] * 11),
            "female_pyramid_data": data.get("female_pyramid_data", [0] * 11),
            "gdp_per_capita": data.get("gdp_per_capita", 0),
            "life_expectancy": data.get("life_expectancy", 70),
            "urbanization": data.get("urbanization", 0),
            "birth_rate": data.get("birth_rate", None),
            "death_rate": data.get("death_rate", None),
            "migration_rate": data.get("migration_rate", None)
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
        data = request.get_json()
        gdp = float(data.get("gdp"))
        life = float(data.get("life"))
        urban = float(data.get("urban"))

        # List of full feature names used during training
        full_features = birth_model.feature_names_in_  # requires scikit-learn >= 1.0

        # Initialize all to 0
        input_data = dict.fromkeys(full_features, 0.0)

        # Set the actual values for the 3 inputs
        input_data['GDP_per_capita'] = gdp
        input_data['Life_expectancy'] = life
        input_data['Urbanization'] = urban

        # Optionally, set the correct region if known — for now, leave region dummy-encoded as 0s

        # Convert to DataFrame
        input_df = pd.DataFrame([input_data])

        # Make predictions
        birth = birth_model.predict(input_df)[0]
        death = death_model.predict(input_df)[0]
        migration = migration_model.predict(input_df)[0]

        return jsonify({
            "birthRate": birth,
            "deathRate": death,
            "migrationRate": migration
        })

    except Exception as e:
        print("Value error in predict:", e)
        return jsonify({"error": "AI Prediction Error: Invalid numeric values provided"}), 400

@app.route("/project_population", methods=["POST"])
def project_population():
    """Project population using test.py logic - predicting rate changes based on growth scenarios"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        population = float(data.get("population", 0))
        initial_birth_rate = float(data.get("birthRate", 20)) / 1000  # Convert to decimal
        initial_death_rate = float(data.get("deathRate", 10)) / 1000  # Convert to decimal  
        initial_migration_rate = float(data.get("migrationRate", 0)) / 1000  # Convert to decimal
        
        # User-specified yearly growth rates (percent)
        user_gdp_growth = float(data.get("gdpGrowth", 2.0))
        user_life_growth = float(data.get("lifeGrowth", 1.0))  
        user_urban_growth = float(data.get("urbanGrowth", 1.0))
        
        years_to_project = int(data.get("yearsToProject", 75))  # Default to 75 years (2025-2100)
        
        if population <= 0:
            return jsonify({"error": "Invalid population value"}), 400
        
        if not all([birth_model, death_model, migration_model]):
            return jsonify({"error": "AI models not available"}), 500

        # Lists to store yearly data
        years = list(range(2025, 2025 + years_to_project + 1))
        populations = [population]
        
        current_population = population
        current_birth_rate = initial_birth_rate
        current_death_rate = initial_death_rate
        current_migration_rate = initial_migration_rate

        # Simulation loop following test.py logic
        for year in range(1, years_to_project + 1):
            try:
                # Prepare input for AI models (growth rates as features)
                X = np.array([[user_gdp_growth, user_life_growth, user_urban_growth]])
                
                # Predict rate changes using AI models
                birth_change = birth_model.predict(X)[0]
                death_change = death_model.predict(X)[0]
                migration_change = migration_model.predict(X)[0]
                
                # Clip changes to reasonable bounds (more conservative)
                birth_change = np.clip(birth_change, -3, 3)    # max ±3% change per year
                death_change = np.clip(death_change, -3, 3)    # max ±3% change per year  
                migration_change = np.clip(migration_change, -1, 1)  # max ±1% for migration
                
                # Apply the changes to current rates
                current_birth_rate *= (1 + birth_change / 100)
                current_death_rate *= (1 + death_change / 100)
                current_migration_rate *= (1 + migration_change / 100)
                
                # Ensure rates stay within realistic demographic bounds
                current_birth_rate = max(0.005, min(0.050, current_birth_rate))  # 5-50 per 1000
                current_death_rate = max(0.005, min(0.050, current_death_rate))   # 5-50 per 1000
                current_migration_rate = max(-0.030, min(0.030, current_migration_rate))  # ±30 per 1000
                
                # Additional demographic reality checks
                # Birth rates typically don't exceed death rates by more than 3% in modern contexts
                if current_birth_rate - current_death_rate > 0.035:
                    current_birth_rate = current_death_rate + 0.035
                
                # Death rates rarely go below 5 per 1000 even in healthiest populations
                if current_death_rate < 0.005:
                    current_death_rate = 0.005
                
                # Calculate new population
                net_rate = current_birth_rate - current_death_rate + current_migration_rate
                current_population = current_population * (1 + net_rate)
                
                # Ensure population doesn't go negative or grow unrealistically
                current_population = max(current_population, 1000)
                if current_population > population * 10:  # Cap at 10x original population
                    current_population = population * 10
                
                populations.append(round(current_population))
                
            except Exception as model_error:
                logger.warning(f"AI model prediction failed for year {year}: {model_error}")
                # Fallback: use previous rates
                net_rate = current_birth_rate - current_death_rate + current_migration_rate
                current_population = current_population * (1 + net_rate)
                current_population = max(current_population, 1000)
                populations.append(round(current_population))

        return jsonify({
            "years": years, 
            "population": populations,
            "metadata": {
                "growth_rates": {
                    "gdp": user_gdp_growth,
                    "life": user_life_growth,
                    "urban": user_urban_growth
                },
                "final_rates": {
                    "birth": round(current_birth_rate * 1000, 3),  # Convert back to per 1000
                    "death": round(current_death_rate * 1000, 3),
                    "migration": round(current_migration_rate * 1000, 3)
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