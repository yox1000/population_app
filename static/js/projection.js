const ageBrackets = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90-99", "100+"];
let populationChart = null;
let projectionChart = null;
let basePopulationData = null; // Store original population data for calculations

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

      // Auto-fill demographic rates
      document.getElementById("birthRate").value = data.birth_rate ?? "20.0";
      document.getElementById("deathRate").value = data.death_rate ?? "10.0";
      document.getElementById("migrationRate").value = data.migration_rate ?? "0.0";

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

function clearData() {
  // Clear all input fields
  ageBrackets.forEach((_, i) => {
    document.getElementById(`male_${i}`).value = '';
    document.getElementById(`female_${i}`).value = '';
  });
  
  // Clear population display
  document.getElementById('current-population').textContent = '—';
  document.getElementById('current-population').dataset.value = '';
  
  // Clear demographic rates
  document.getElementById("birthRate").value = '20.0';
  document.getElementById("deathRate").value = '10.0';
  document.getElementById("migrationRate").value = '0.0';
  
  // Clear growth rates
  document.getElementById("gdpGrowth").value = '2.0';
  document.getElementById("lifeGrowth").value = '1.0';
  document.getElementById("urbanGrowth").value = '1.0';
  
  // Hide stats
  document.getElementById('stats').style.display = 'none';
  
  // Clear charts
  if (populationChart) {
    populationChart.destroy();
    populationChart = null;
  }
  if (projectionChart) {
    projectionChart.destroy();
    projectionChart = null;
  }
  
  // Clear base population data
  basePopulationData = null;
  
  // Hide click instruction
  document.getElementById('click-instruction').style.display = 'none';
}

function calculateProjectedDemographics(yearsDiff, birthRate, deathRate) {
  if (!basePopulationData) return null;
  
  const projected = {
    male: [...basePopulationData.male],
    female: [...basePopulationData.female]
  };
  
  // Simple aging model: shift populations up age brackets
  const ageShift = Math.floor(yearsDiff / 10); // Each bracket represents 10 years
  
  if (ageShift > 0 && ageShift < projected.male.length) {
    // Create temporary arrays for the shifted data
    const newMale = new Array(projected.male.length).fill(0);
    const newFemale = new Array(projected.female.length).fill(0);
    
    // Shift existing populations up by ageShift brackets
    for (let i = 0; i < projected.male.length - ageShift; i++) {
      // Apply survival rate (reduce by death rate over the time period)
      const survivalRate = Math.pow(1 - deathRate / 1000, yearsDiff);
      newMale[i + ageShift] = projected.male[i] * survivalRate;
      newFemale[i + ageShift] = projected.female[i] * survivalRate;
    }
    
    // Calculate births for younger age groups
    const totalReproductiveAge = projected.male.slice(2, 6).reduce((a, b) => a + b, 0) + 
                                projected.female.slice(2, 6).reduce((a, b) => a + b, 0); // Ages 20-59
    
    if (totalReproductiveAge > 0) {
      const annualBirths = totalReproductiveAge * (birthRate / 1000);
      const totalBirths = annualBirths * yearsDiff;
      
      // Distribute births across younger age groups
      for (let i = 0; i < Math.min(ageShift, projected.male.length); i++) {
        const birthFraction = 1 / ageShift; // Evenly distribute across age groups
        newMale[i] = totalBirths * 0.51 * birthFraction; // 51% male births
        newFemale[i] = totalBirths * 0.49 * birthFraction; // 49% female births
      }
    }
    
    projected.male = newMale;
    projected.female = newFemale;
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

  // Get initial demographic rates
  const birthRate = parseFloat(document.getElementById("birthRate").value);
  const deathRate = parseFloat(document.getElementById("deathRate").value);
  const migrationRate = parseFloat(document.getElementById("migrationRate").value);

  // Get growth rates (following test.py logic)
  const gdpGrowth = parseFloat(document.getElementById("gdpGrowth").value);
  const lifeGrowth = parseFloat(document.getElementById("lifeGrowth").value);
  const urbanGrowth = parseFloat(document.getElementById("urbanGrowth").value);
  
  const yearsToProject = parseInt(document.getElementById("yearsToProject").value);

  fetch("/project_population", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      population: pop2025,
      birthRate: birthRate,
      deathRate: deathRate,
      migrationRate: migrationRate,
      gdpGrowth: gdpGrowth,
      lifeGrowth: lifeGrowth,
      urbanGrowth: urbanGrowth,
      yearsToProject: yearsToProject
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) {
      alert("Projection error: " + data.error);
      return;
    }
    plotProjectionChart(data.years, data.population, data.metadata);
  })
  .catch(err => {
    console.error("Fetch error:", err);
    alert("Failed to fetch population projection.");
  });
}

function plotProjectionChart(years, population, metadata) {
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
          text: `AI-Powered Population Projection (Growth Rates: GDP ${metadata.growth_rates.gdp}%, Life ${metadata.growth_rates.life}%, Urban ${metadata.growth_rates.urban}%)`,
          font: { size: 14, weight: 'bold' }
        },
        subtitle: {
          display: true,
          text: `Final Rates: Birth ${metadata.final_rates.birth}‰, Death ${metadata.final_rates.death}‰, Migration ${metadata.final_rates.migration}‰`,
          font: { size: 12 },
          color: '#666'
        }
      },
      scales: {
        y: { 
          title: { display: true, text: "Population" },
          ticks: {
            callback: function(value) {
              return value.toLocaleString();
            }
          }
        },
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

// Initialize the table when the page loads
window.onload = initializeTable;