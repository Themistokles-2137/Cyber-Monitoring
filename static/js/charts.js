// Charts for Indian Cyber Incident Monitor Dashboard

/**
 * Initialize the sector distribution chart
 * @param {string} chartId - The ID of the canvas element
 * @param {array} labels - Array of sector labels
 * @param {array} data - Array of counts for each sector
 */
function initSectorChart(chartId, labels, data) {
  const ctx = document.getElementById(chartId).getContext('2d');
  
  // Generate colors for each sector
  const colors = generateColors(labels.length);
  
  return new Chart(ctx, {
    type: 'pie',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors,
        borderWidth: 1,
        borderColor: '#343a40'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            color: '#c8c8c8'
          }
        },
        title: {
          display: true,
          text: 'Incidents by Sector',
          color: '#c8c8c8',
          font: {
            size: 16
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const value = context.raw || 0;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = Math.round((value / total) * 100);
              return `${label}: ${value} (${percentage}%)`;
            }
          }
        }
      }
    }
  });
}

/**
 * Initialize the severity distribution chart
 * @param {string} chartId - The ID of the canvas element
 * @param {array} labels - Array of severity labels
 * @param {array} data - Array of counts for each severity
 */
function initSeverityChart(chartId, labels, data) {
  const ctx = document.getElementById(chartId).getContext('2d');
  
  // Define colors for severity levels
  const severityColors = {
    'Critical': '#dc3545',
    'High': '#fd7e14',
    'Medium': '#ffc107',
    'Low': '#28a745',
    'Informational': '#6c757d',
    'Unknown': '#6c757d'
  };
  
  // Map severity labels to colors
  const colors = labels.map(label => severityColors[label] || '#6c757d');
  
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors,
        borderWidth: 1,
        borderColor: '#343a40'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            color: '#c8c8c8'
          }
        },
        title: {
          display: true,
          text: 'Incidents by Severity',
          color: '#c8c8c8',
          font: {
            size: 16
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const value = context.raw || 0;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = Math.round((value / total) * 100);
              return `${label}: ${value} (${percentage}%)`;
            }
          }
        }
      }
    }
  });
}

/**
 * Initialize the time trend chart
 * @param {string} chartId - The ID of the canvas element
 * @param {array} labels - Array of date labels
 * @param {array} data - Array of counts for each date
 */
function initTrendChart(chartId, labels, data) {
  const ctx = document.getElementById(chartId).getContext('2d');
  
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Incidents',
        data: data,
        backgroundColor: 'rgba(13, 110, 253, 0.2)',
        borderColor: '#0d6efd',
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: '#0d6efd',
        tension: 0.4,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          },
          ticks: {
            color: '#c8c8c8'
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          },
          ticks: {
            color: '#c8c8c8',
            precision: 0
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        title: {
          display: true,
          text: 'Incident Trend Over Time',
          color: '#c8c8c8',
          font: {
            size: 16
          }
        }
      }
    }
  });
}

/**
 * Initialize the source distribution chart
 * @param {string} chartId - The ID of the canvas element
 * @param {array} labels - Array of source labels
 * @param {array} data - Array of counts for each source
 */
function initSourceChart(chartId, labels, data) {
  const ctx = document.getElementById(chartId).getContext('2d');
  
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Incidents',
        data: data,
        backgroundColor: 'rgba(13, 202, 240, 0.7)',
        borderColor: 'rgba(13, 202, 240, 1)',
        borderWidth: 1
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          beginAtZero: true,
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          },
          ticks: {
            color: '#c8c8c8',
            precision: 0
          }
        },
        y: {
          grid: {
            display: false
          },
          ticks: {
            color: '#c8c8c8'
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        title: {
          display: true,
          text: 'Top Sources of Incidents',
          color: '#c8c8c8',
          font: {
            size: 16
          }
        }
      }
    }
  });
}

/**
 * Generate random colors for charts
 * @param {number} count - The number of colors to generate
 * @returns {array} - Array of color strings
 */
function generateColors(count) {
  // Predefined colors for consistency
  const baseColors = [
    '#0d6efd', // Blue
    '#6610f2', // Indigo
    '#6f42c1', // Purple
    '#d63384', // Pink
    '#dc3545', // Red
    '#fd7e14', // Orange
    '#ffc107', // Yellow
    '#198754', // Green
    '#20c997', // Teal
    '#0dcaf0', // Cyan
    '#adb5bd', // Gray
    '#495057'  // Dark gray
  ];
  
  // If we need more colors than predefined, generate them
  let colors = [...baseColors];
  
  while (colors.length < count) {
    const r = Math.floor(Math.random() * 255);
    const g = Math.floor(Math.random() * 255);
    const b = Math.floor(Math.random() * 255);
    colors.push(`rgba(${r}, ${g}, ${b}, 0.7)`);
  }
  
  return colors.slice(0, count);
}

/**
 * Format date for display in charts
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted date string
 */
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Update a chart with new data
 * @param {Chart} chart - Chart.js instance
 * @param {array} labels - New labels
 * @param {array} data - New data
 */
function updateChart(chart, labels, data) {
  chart.data.labels = labels;
  chart.data.datasets[0].data = data;
  chart.update();
}

/**
 * Fetch data from an API endpoint and update a chart
 * @param {string} endpoint - API endpoint URL
 * @param {Chart} chart - Chart.js instance to update
 */
function fetchChartData(endpoint, chart) {
  fetch(endpoint)
    .then(response => response.json())
    .then(data => {
      updateChart(chart, data.labels, data.data);
    })
    .catch(error => {
      console.error('Error fetching chart data:', error);
    });
}
