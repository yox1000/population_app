  const ageBrackets = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90-99", "100+"];
  let populationChart = null;
  let projectionChart = null;
  let basePopulationData = null; // Store original population data for calculations

  const presets = {
    afghanistan: {
      population: 42270000,
      male: [17.2, 12.9, 7.8, 4.8, 3.4, 2.2, 1.6, 0.7, 0.2, 0.1, 0.1],
      female: [16.3, 12.0, 8.4, 4.7, 3.6, 2.2, 1.2, 0.5, 0.1, 0.1, 0.0]
    },
    ecuador: {
      population: 18100000,
      male: [9.9, 9.8, 8.6, 7.2, 5.7, 4.4, 3.5, 1.6, 0.7, 0.3, 0.1],
      female: [9.5, 9.6, 7.8, 6.8, 5.0, 3.1, 2.0, 1.3, 0.2, 0.1, 0.0]
    },
    italy: {
      population: 58850000,
      male: [4.3, 5.2, 5.5, 6.0, 7.7, 8.3, 6.0, 4.9, 2.7, 1.2, 0.2],
      female: [4.0, 4.8, 5.8, 6.6, 7.9, 7.9, 5.1, 4.1, 2.1, 1.0, 0.1]
    },
    qatar: {
      population: 2820000,
      male: [5.5, 3.9, 22.0, 12.9, 7.2, 2.8, 1.5, 0.3, 0.1, 0.0, 0.0],
      female: [5.3, 2.4, 7.4, 8.2, 4.5, 1.8, 0.7, 0.1, 0.1, 0.0, 0.0]
    }
  };

  function initializeTable() {
    const tbody = document.getElementById('age-table');
    tbody.innerHTML = '';
    ageBrackets.forEach((bracket, i) => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td><strong>${bracket}</strong></td>
        <td><input type="number" id="male_${i}" step="0.1" min="0" max="100"></td>
        <td><input type="number" id="female_${i}" step="0.1" min="0" max="100"></td>
      `;
      tbody.appendChild(row);
    });
  }

  function loadPreset(name) {
  fetch(`/get-country-data/${name}`)
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert(`Error loading ${name}: ${data.error}`);
        return;
      }

      document.getElementById('current-population').textContent = data.population.toLocaleString();
      document.getElementById('current-population').dataset.value = data.population;

      // Auto-fill the economic indicators
      document.getElementById("gdp").value = data.gdp_per_capita ?? "";
      document.getElementById("life").value = data.life_expectancy ?? "";
      document.getElementById("urban").value = data.urbanization ?? "";

      // Auto-fill demographic rates
      document.getElementById("birthRate").value = data.birth_rate ?? "";
      document.getElementById("deathRate").value = data.death_rate ?? "";
      document.getElementById("migrationRate").value = data.migration_rate ?? "";
      document.getElementById("rateYear").textContent = data.year ?? "2025"; // default to 2025

      basePopulationData = {
        male: [...data.male_pyramid_data],
        female: [...data.female_pyramid_data]
      };

      // Fill the age bracket inputs
      ageBrackets.forEach((_, i) => {
        document.getElementById(`male_${i}`).value = data.male_pyramid_data[i];
        document.getElementById(`female_${i}`).value = data.female_pyramid_data[i];
      });

      // Update statistics and generate chart
      calculateStats();
      generateChart(new Event("submit"));
    })
    .catch(error => {
      console.error('Error fetching country data:', error);
      alert(`Failed to load data for ${name}. Please try again.`);
    });
}

  function calculateProjectedDemographics(yearsDiff, birthRate, deathRate) {
    if (!basePopulationData) return null;
    
    const projected = {
      male: [...basePopulationData.male],
      female: [...basePopulationData.female]
    };
    
    // Simple aging model: shift populations up age brackets
    const ageShift = Math.floor(yearsDiff / 10); // Each bracket represents 10 years
    
    if (ageShift > 0) {
      // Age the population by shifting brackets
      for (let shift = 0; shift < ageShift; shift++) {
        // Shift all brackets up by one
        for (let i = projected.male.length - 1; i > 0; i--) {
          projected.male[i] = projected.male[i - 1] * (1 - deathRate / 100);
          projected.female[i] = projected.female[i - 1] * (1 - deathRate / 100);
        }
        
        // New births (0-9 age group)
        const totalPop = projected.male.reduce((a, b) => a + b, 0) + projected.female.reduce((a, b) => a + b, 0);
        const newBirths = totalPop * (birthRate / 100);
        projected.male[0] = newBirths * 0.51; // Slightly more males born
        projected.female[0] = newBirths * 0.49;
      }
    }
    
    return projected;
  }

  function updatePyramidForYear(year) {
    if (!basePopulationData) return;
    
    const yearsDiff = year - 2025;
    const birthRate = parseFloat(document.getElementById('birthRate').value);
    const deathRate = parseFloat(document.getElementById('deathRate').value);
    
    const projected = calculateProjectedDemographics(yearsDiff, birthRate, deathRate);
    
    if (projected) {
      // Update the input fields
      ageBrackets.forEach((_, i) => {
        document.getElementById(`male_${i}`).value = projected.male[i].toFixed(1);
        document.getElementById(`female_${i}`).value = projected.female[i].toFixed(1);
      });
      
      // Update the chart
      generateChart(new Event("submit"));
      
      // Update the title to show the year
      if (populationChart) {
        populationChart.options.plugins.title.text = `Population Pyramid - Year ${year}`;
        populationChart.update();
      }
    }
  }

  function generateChart(e) {
    e.preventDefault();

    // Collect and reverse data
    const maleData = [];
    const femaleData = [];
    const labels = [];

    for (let i = ageBrackets.length - 1; i >= 0; i--) {
      const maleVal = parseFloat(document.getElementById(`male_${i}`).value) || 0;
      const femaleVal = parseFloat(document.getElementById(`female_${i}`).value) || 0;
      maleData.push(-maleVal); // negative for left bar
      femaleData.push(femaleVal);
      labels.push(ageBrackets[i]);
    }

    if (populationChart) populationChart.destroy();

    const ctx = document.getElementById('populationChart').getContext('2d');
    populationChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Male',
            data: maleData,
            backgroundColor: 'rgba(33, 150, 243, 0.8)',
            borderColor: 'rgba(33, 150, 243, 1)',
            borderWidth: 1
          },
          {
            label: 'Female',
            data: femaleData,
            backgroundColor: 'rgba(233, 30, 99, 0.8)',
            borderColor: 'rgba(233, 30, 99, 1)',
            borderWidth: 1
          }
        ]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        scales: {
          x: {
            stacked: true,
            ticks: {
              callback: val => Math.abs(val) + '%'
            },
            title: {
              display: true,
              text: 'Population %',
              font: {
                size: 14,
                weight: 'bold'
              }
            }
          },
          y: {
            stacked: true,
            title: {
              display: true,
              text: 'Age Group',
              font: {
                size: 14,
                weight: 'bold'
              }
            }
          }
        },
        plugins: {
          title: {
            display: true,
            text: 'Population Pyramid - 2025',
            font: {
              size: 18,
              weight: 'bold'
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return context.dataset.label + ': ' + Math.abs(context.parsed.x) + '%';
              }
            }
          },
          legend: {
            display: true,
            position: 'top'
          }
        }
      }
    });

    calculateStats();
  }

  function calculateStats() {
    const males = ageBrackets.map((_, i) => parseFloat(document.getElementById(`male_${i}`).value) || 0);
    const females = ageBrackets.map((_, i) => parseFloat(document.getElementById(`female_${i}`).value) || 0);
    const maleTotal = males.reduce((a, b) => a + b, 0);
    const femaleTotal = females.reduce((a, b) => a + b, 0);
    const total = maleTotal + femaleTotal;
    const youth = males[0] + males[1] + females[0] + females[1];

    document.getElementById('total-pop').textContent = total.toFixed(1);
    document.getElementById('male-total').textContent = maleTotal.toFixed(1);
    document.getElementById('female-total').textContent = femaleTotal.toFixed(1);
    document.getElementById('youth-ratio').textContent = ((youth / total) * 100).toFixed(1) + '%';
    document.getElementById('stats').style.display = 'flex';
  }

function generateProjectionChart() {
    const pop2025 = parseFloat(document.getElementById("current-population").dataset.value);
    if (!pop2025) return alert("Load a preset to get starting population.");

    // Instead of local growth, send inputs & scenarios to backend
    const gdp = parseFloat(document.getElementById("gdp").value);
    const life = parseFloat(document.getElementById("life").value);
    const urban = parseFloat(document.getElementById("urban").value);

    const gdpScenario = document.getElementById("gdpScenario").value;
    const lifeScenario = document.getElementById("lifeScenario").value;
    const urbanScenario = document.getElementById("urbanScenario").value;

    fetch("/project_population", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        population: pop2025,
        gdp, life, urban,
        gdpScenario,
        lifeScenario,
        urbanScenario
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        alert("Projection error: " + data.error);
        return;
      }
      plotProjectionChart(data.years, data.population);
    })
    .catch(err => {
      console.error("Fetch error:", err);
      alert("Failed to fetch population projection.");
    });
  }

  function plotProjectionChart(years, population) {
    if (projectionChart) projectionChart.destroy();

    const ctx = document.getElementById('projectionChart').getContext('2d');
    projectionChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: years,
        datasets: [{
          label: 'Projected Population',
          data: population,
          fill: true,
          borderColor: '#4CAF50',
          backgroundColor: 'rgba(76, 175, 80, 0.3)',
          tension: 0.4,
          pointRadius: 5,
          pointHoverRadius: 8,
          pointBackgroundColor: '#4CAF50',
          pointBorderColor: '#2E7D32',
          pointBorderWidth: 2
        }]
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: "Projected Population (2025–2100) - Click points to update pyramid",
            font: { size: 16, weight: 'bold' }
          }
        },
        scales: {
          y: { title: { display: true, text: "Population" } },
          x: { title: { display: true, text: "Year" } }
        },
        interaction: {
          mode: 'nearest',
          intersect: true
        },
        onClick: (event, activeElements) => {
          if (activeElements.length > 0) {
            const idx = activeElements[0].index;
            const year = years[idx];
            updatePyramidForYear(year);
          }
        }
      }
    });

    document.getElementById('click-instruction').style.display = 'block';
  }

  function predictRates() {
    const gdp = parseFloat(document.getElementById("gdp").value);
    const life = parseFloat(document.getElementById("life").value);
    const urban = parseFloat(document.getElementById("urban").value);

    fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gdp, life, urban })
    })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        alert("AI Prediction Error: " + data.error);
        return;
      }
      document.getElementById("birthRate").value = data.birthRate.toFixed(2);
      document.getElementById("deathRate").value = data.deathRate.toFixed(2);
      document.getElementById("migrationRate").value = data.migrationRate.toFixed(2);
    })
    .catch(err => {
      console.error("Fetch error:", err);
      alert("Failed to fetch AI prediction.");
    });
}


  window.onload = initializeTable;