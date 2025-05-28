/**
 * Dashboard functionality for Indian Cyber Incident Monitor
 */

/**
 * Set up dashboard event listeners and functionality
 * @param {Chart} trendChart - The time trend chart object
 */
function setupDashboardEvents(trendChart) {
    // Set up refresh button
    const refreshButton = document.getElementById('refreshDashboard');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            refreshDashboardData();
        });
    }
    
    // Set up time period buttons for trend chart
    const periodButtons = document.querySelectorAll('[data-period]');
    periodButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update active state
            periodButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Get selected period
            const period = this.getAttribute('data-period');
            updateTrendChart(trendChart, period);
        });
    });
}

/**
 * Refresh all dashboard data
 */
function refreshDashboardData() {
    // Show loading state
    const refreshButton = document.getElementById('refreshDashboard');
    if (refreshButton) {
        const originalHtml = refreshButton.innerHTML;
        refreshButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Refreshing...';
        refreshButton.disabled = true;
        
        // Reload the page after a short delay
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    }
}

/**
 * Update the trend chart with new time period data
 * @param {Chart} chart - The chart to update
 * @param {string} period - The time period in days
 */
function updateTrendChart(chart, period) {
    // Show loading state
    chart.data.datasets[0].data = [];
    chart.update();
    
    // Fetch updated data for the selected period
    fetch(`/dashboard/time_trend?days=${period}`)
        .then(response => response.json())
        .then(data => {
            // Update chart data
            chart.data.labels = data.labels;
            chart.data.datasets[0].data = data.data;
            
            // Set appropriate X-axis time unit based on period
            if (period <= 30) {
                chart.options.scales.x.time = {
                    unit: 'day'
                };
            } else if (period <= 90) {
                chart.options.scales.x.time = {
                    unit: 'week'
                };
            } else {
                chart.options.scales.x.time = {
                    unit: 'month'
                };
            }
            
            chart.update();
        })
        .catch(error => {
            console.error('Error updating trend chart:', error);
        });
}

/**
 * Format numbers for display (add thousands separator)
 * @param {number} number - The number to format
 * @returns {string} - Formatted number string
 */
function formatNumber(number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Update dashboard statistics without reloading the page
 * @param {Object} stats - Object containing updated statistics
 */
function updateDashboardStats(stats) {
    // Update total incidents
    const totalElement = document.querySelector('.card-body h2:first-of-type');
    if (totalElement && stats.total_incidents) {
        totalElement.textContent = formatNumber(stats.total_incidents);
    }
    
    // Update recent incidents
    const recentElement = document.querySelector('.card-body h2:nth-of-type(2)');
    if (recentElement && stats.recent_count) {
        recentElement.textContent = formatNumber(stats.recent_count);
    }
    
    // Update high severity count
    const highSevElement = document.querySelector('.card-body h2:nth-of-type(3)');
    if (highSevElement && stats.critical_high) {
        highSevElement.textContent = formatNumber(stats.critical_high);
    }
}

/**
 * Initialize actor distribution chart
 * @param {string} chartId - The ID of the canvas element
 * @param {array} labels - Array of actor labels
 * @param {array} data - Array of counts for each actor
 */
function initActorChart(chartId, labels, data) {
    const ctx = document.getElementById(chartId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Incidents',
                data: data,
                backgroundColor: 'rgba(253, 126, 20, 0.7)',
                borderColor: 'rgba(253, 126, 20, 1)',
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
                    text: 'Top Threat Actors',
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
 * Initialize monthly trend chart
 * @param {string} chartId - The ID of the canvas element
 * @param {array} labels - Array of month labels
 * @param {array} data - Array of counts for each month
 */
function initMonthlyTrendChart(chartId, labels, data) {
    const ctx = document.getElementById(chartId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Incidents',
                data: data,
                backgroundColor: 'rgba(13, 110, 253, 0.7)',
                borderColor: 'rgba(13, 110, 253, 1)',
                borderWidth: 1
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
                    text: 'Monthly Incident Trend',
                    color: '#c8c8c8',
                    font: {
                        size: 16
                    }
                }
            }
        }
    });
}
