/* TextShield Chart Initialization - Dashboard Specific */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard charts
    initDashboardRiskChart();
    initDashboardTypeChart();
});

/* Initialize dashboard risk chart */
function initDashboardRiskChart() {
    const ctx = document.getElementById('dashboard-risk-chart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Very Low', 'Low', 'Medium', 'High', 'Critical'],
            datasets: [{
                label: 'Message Count',
                data: [12, 34, 56, 23, 8],
                backgroundColor: [
                    'rgba(34, 197, 94, 0.5)',
                    'rgba(74, 222, 128, 0.5)',
                    'rgba(245, 158, 11, 0.5)',
                    'rgba(239, 68, 68, 0.5)',
                    'rgba(185, 28, 28, 0.5)'
                ],
                borderColor: [
                    'rgba(34, 197, 94, 1)',
                    'rgba(74, 222, 128, 1)',
                    'rgba(245, 158, 11, 1)',
                    'rgba(239, 68, 68, 1)',
                    'rgba(185, 28, 28, 1)'
                ],
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

/* Initialize dashboard type chart */
function initDashboardTypeChart() {
    const ctx = document.getElementById('dashboard-type-chart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['SMS', 'Email', 'Text', 'Other'],
            datasets: [{
                label: 'Message Type Distribution',
                data: [34, 28, 45, 12],
                backgroundColor: [
                    'rgba(34, 197, 94, 0.5)',
                    'rgba(34, 197, 94, 0.5)',
                    'rgba(34, 197, 94, 0.5)',
                    'rgba(107, 114, 128, 0.5)'
                ],
                borderColor: [
                    'rgba(34, 197, 94, 1)',
                    'rgba(34, 197, 94, 1)',
                    'rgba(34, 197, 94, 1)',
                    'rgba(107, 114, 128, 1)'
                ],
                borderWidth: 1
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