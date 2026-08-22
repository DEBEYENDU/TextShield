/* TextShield Dashboard JavaScript */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard on load
    initDashboardStats();
    initRiskDistribution();
    updateClock();
});

/* Update current time */
function updateClock() {
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const dateString = now.toLocaleDateString(undefined, options);
    document.getElementById('current-date').innerText = dateString;
    
    setTimeout(updateClock, 60000);
}

/* Initialize dashboard stats */
function initDashboardStats() {
    // Fetch dashboard stats via AJAX
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStats(data.data);
            }
        })
        .catch(error => {
            console.error('Failed to fetch dashboard stats:', error);
        });
}

/* Update statistic cards */
function updateStats(stats) {
    const elements = {
        'stat-total': stats.total_analyzed || '-',
        'stat-spam': stats.spam_count || '-',
        'stat-ham': stats.ham_count || '-',
        'stat-pct': stats.spam_percentage !== undefined ? stats.spam_percentage + '%' : '-'
    };
    
    Object.keys(elements).forEach(key => {
        const el = document.getElementById(key);
        if (el) el.innerText = elements[key];
    });
}

/* Initialize risk distribution chart */
function initRiskDistribution() {
    fetch('/api/risk-distribution')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                initRiskChartData(data.data);
            }
        })
        .catch(error => {
            console.error('Failed to fetch risk distribution:', error);
        });
}

/* Initialize risk chart with data */
function initRiskChartData(data) {
    const ctx = document.getElementById('dashboard-risk-chart');
    if (!ctx) return;
    
    const riskLevels = ['Very Low', 'Low', 'Medium', 'High', 'Critical'];
    const counts = riskLevels.map(level => data.risk_counts[level] || 0);
    const colors = [
        'rgba(34, 197, 94, 0.5)',
        'rgba(74, 222, 128, 0.5)',
        'rgba(245, 158, 11, 0.5)',
        'rgba(239, 68, 68, 0.5)',
        'rgba(185, 28, 28, 0.5)'
    ];
    const borderColors = [
        'rgba(34, 197, 94, 1)',
        'rgba(74, 222, 128, 1)',
        'rgba(245, 158, 11, 1)',
        'rgba(239, 68, 68, 1)',
        'rgba(185, 28, 28, 1)'
    ];
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: riskLevels,
            datasets: [{
                label: 'Message Count',
                data: counts,
                backgroundColor: colors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'var(--primary)',
                    titleColor: '#f8fafc',
                    bodyColor: '#e2e8f0'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#64748b'
                    },
                    grid: {
                        color: 'var(--border)'
                    }
                },
                x: {
                    ticks: {
                        color: '#64748b'
                    },
                    grid: {
                        color: 'var(--border)'
                    }
                }
            }
        }
    });
}

/* Initialize type distribution chart */
function initTypeDistribution(data) {
    const ctx = document.getElementById('dashboard-type-chart');
    if (!ctx) return;
    
    const typeLabels = Object.keys(data.type_counts || {});
    const typeCounts = Object.values(data.type_counts || {});
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: typeLabels,
            datasets: [{
                label: 'Message Type Distribution',
                data: typeCounts,
                backgroundColor: typeColors(typeLabels)
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

/* Get color for type */
function typeColors(labels) {
    const colors = {
        'SMS': 'rgba(34, 197, 94, 0.5)',
        'Email': 'rgba(34, 197, 94, 0.5)',
        'Text': 'rgba(34, 197, 94, 0.5)',
        'Other': 'rgba(107, 114, 128, 0.5)'
    };
    return labels.map(label => colors[label] || 'rgba(107, 114, 128, 0.5)');
}