import numpy as np
import joblib
import matplotlib.pyplot as plt

# Load pre-trained models
birth_model = joblib.load('birth_model.pkl')
death_model = joblib.load('death_model.pkl')
migration_model = joblib.load('migration_model.pkl')

# Example starting data for a country
population = 1_000_000
birth_rate = 0.02
death_rate = 0.01
migration_rate = 0.001
GDP_per_capita = 50000
life_expectancy = 75
urbanization = 0.6

# User-specified yearly growth rates (percent)
user_GDP_growth = -2.0
user_life_growth = 1.0
user_urban_growth = 1.0

years_to_project = 10
years = list(range(2026, 2026 + years_to_project))

# Lists to store yearly data for plotting
pop_list = []
birth_list = []
death_list = []
migration_list = []

# Simulation loop
for year in range(1, years_to_project + 1):
    X = np.array([[user_GDP_growth, user_life_growth, user_urban_growth]])
    
    birth_change = birth_model.predict(X)[0]
    death_change = death_model.predict(X)[0]
    migration_change = migration_model.predict(X)[0]

    birth_change = np.clip(birth_change, -5, 5)    # max ±5% change per year
    death_change = np.clip(death_change, -5, 5)
    migration_change = np.clip(migration_change, -2, 2)  # smaller for migration
    
    birth_rate *= 1 + birth_change / 100
    death_rate *= 1 + death_change / 100
    migration_rate *= 1 + migration_change / 100
    
    population = population * (1 + birth_rate - death_rate + migration_rate)
    
    pop_list.append(population)
    birth_list.append(birth_rate)
    death_list.append(death_rate)
    migration_list.append(migration_rate)
    
    print(f"{2025 + year} | {int(population)} | {birth_rate:.4f} | {death_rate:.4f} | {migration_rate:.4f}")

# Plotting 4 charts in a 2x2 grid
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Population chart
axes[0, 0].plot(years, pop_list, color='blue', linewidth=2)
axes[0, 0].set_title('Population')
axes[0, 0].set_xlabel('Year')
axes[0, 0].set_ylabel('Population')
axes[0, 0].grid(True)

# Birth rate chart
axes[0, 1].plot(years, birth_list, color='green', linewidth=2)
axes[0, 1].set_title('Birth Rate')
axes[0, 1].set_xlabel('Year')
axes[0, 1].set_ylabel('Rate')
axes[0, 1].grid(True)

# Death rate chart
axes[1, 0].plot(years, death_list, color='red', linewidth=2)
axes[1, 0].set_title('Death Rate')
axes[1, 0].set_xlabel('Year')
axes[1, 0].set_ylabel('Rate')
axes[1, 0].grid(True)

# Migration rate chart
axes[1, 1].plot(years, migration_list, color='orange', linewidth=2)
axes[1, 1].set_title('Migration Rate')
axes[1, 1].set_xlabel('Year')
axes[1, 1].set_ylabel('Rate')
axes[1, 1].grid(True)

plt.tight_layout()
plt.show()

