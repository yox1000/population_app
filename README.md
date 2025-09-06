🌍 Population Projection & Pyramid App

Population_app lets you explore population structures and future projections for selected countries.
It combines population pyramids (age/sex distributions) with long-term population forecasts (2025–2100) under different economic (through GDP per capita), health(through life expectancy), and urbanization scenarios.

✨ Features

📊 Population Pyramid: Automatically generated for a selected country (e.g., Italy, Qatar, Ecuador, Afghanistan).

📈 Population Projection: Forecasts population to 2100 based on:

GDP growth scenarios

Life expectancy scenarios

Urbanization scenarios

Users are able to select their own rates but there are bounds for each in order to ensure some level of realism.

🤖 AI-Enhanced Predictions: Used RandomFrest on historical demographic data to build a model estimating birth, death, and migration rates from GDP, life expectancy, and urbanization.

🗑️ Clear Data: Reset inputs and remove charts at any time.

🛠️ Tech Stack

Backend: Python (Flask framework)

Frontend: HTML, CSS, JS

Machine Learning: scikit-learn models (RandomForestRegressor)

Data Storage: JSON (country demographics), csv (demographics_multi_year training data)

How to Run:

git clone <repo-url>

cd project

pip install -r requirements.txt

flask run

In your browser, go to:
http://127.0.0.1:5000

Example Workflow:

Select a preset country (Italy, Qatar, Ecuador, Afghanistan., China, India).

The population pyramid loads automatically.

Choose growth scenarios (GDP, life, urbanization).

The projection chart updates with projected population through 2100.

Use Clear to reset the app.

🔮 Future Enhancements

Add more countries dynamically from datasets (UN, World Bank).

Include more data for models to train on.

Add more variables, as there are countless variables that can affect population change.
Just these three initial variables is a simplistic model.

Fix age bracket projection in population pyramid 

Compare multiple countries side-by-side.

Export charts as PNG/PDF.

📝 License

MIT License – free to use, modify, and share.
