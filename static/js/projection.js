const scenarioRates = {
  gdp: {
    high: 0.025, medium: 0.015, low: 0.005, stagnant: 0, decline: -0.01
  },
  life: {
    high: 0.5, medium: 0.3, low: 0.1, stagnant: 0, decline: -0.2
  },
  urban: {
    high: 0.8, medium: 0.5, low: 0.2, stagnant: 0, decline: -0.5
  }
};

async function getInitialData(country) {
  const res = await fetch(`/get-country-data/${country}`);
  const data = await res.json();
  return {
    gdp: data.gdp,
    life: data.life,
    urban: data.urban,
    population: data.population
  };
}

window.projectPopulation = async function (country) {
  const selectedGdp = document.getElementById('gdpScenario').value;
  const selectedLife = document.getElementById('lifeScenario').value;
  const selectedUrban = document.getElementById('urbanScenario').value;

  const growthRates = {
    gdp: scenarioRates.gdp[selectedGdp],
    life: scenarioRates.life[selectedLife],
    urban: scenarioRates.urban[selectedUrban]
  };

  const { gdp, life, urban, population } = await getInitialData(country);
  let currentGDP = gdp;
  let currentLife = life;
  let currentUrban = urban;
  let currentPop = population;
  const projections = [{ year: 2025, population: currentPop }];

  for (let year = 2030; year <= 2100; year += 5) {
    currentGDP *= (1 + growthRates.gdp);
    currentLife += growthRates.life;
    currentUrban += growthRates.urban;

    const response = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        gdp: currentGDP,
        life: currentLife,
        urban: currentUrban
      })
    });

    const rates = await response.json();
    const birthRate = rates.birthRate;
    const deathRate = rates.deathRate;
    const migrationRate = rates.migrationRate;

    const netRate = (birthRate - deathRate + migrationRate) / 1000;
    const delta = currentPop * netRate * 5;
    currentPop += delta;
    projections.push({ year: year, population: currentPop });
  }

  drawPopulationChart(projections);
};

function drawPopulationChart(data) {
  const ctx = document.getElementById('populationChart').getContext('2d');
  if (window.populationChart) {
    window.populationChart.destroy();
  }
  window.populationChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.year),
      datasets: [{
        label: 'Projected Population',
        data: data.map(d => d.population),
        borderColor: 'blue',
        fill: false
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { title: { display: true, text: 'Population' } },
        x: { title: { display: true, text: 'Year' } }
      }
    }
  });
}
