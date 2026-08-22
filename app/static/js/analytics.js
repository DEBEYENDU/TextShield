/* TextShield Analytics JavaScript - Analytics Dashboard Page */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize analytics on load
    initAnalytics();
    
    // Initialize charts
    initAllCharts();
});

/* Initialize analytics */
function initAnalytics() {
    fetch('/api/analytics')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayStats(data.stats);
                initCharts(data.charts);
            }
        })
        .catch(error => {
            console.error('Failed to fetch analytics:', error);
        });
})

/* Display statistics */
function displayStats(stats) {
    const statsEl = document.getElementById('analytics-stats');
    if (!statsEl) return;
    
    statsEl.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${stats.total_analyzed || 0}</div>
            <div class="stat-label">Total Analyzed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value stat-red">${stats.total_spam || 0}</div>
            <div class="stat-label">Spam</div>
        </div>
        <div class="stat-card">
            <div class="stat-value stat-green">${stats.total_ham || 0}</div>
            <div class="stat-label">Ham</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${(stats.avg_confidence * 100).toFixed(1)}%</div>
            <div class="stat-label">Avg Confidence</div>
        </div>
    `;
}

/* Initialize all charts */
function initAllCharts(chartData) {
    initSpamVsHamChart(chartData?.spam_vs_ham);
    initRiskDistributionChart(chartData?.risk_distribution);
    initConfidenceDistributionChart(chartData?.confidence_distribution);
    initModelConfidenceOverTimeChart(chartData?.model_confidence_over_time);
    initMessageTypeChart(chartData?.message_type_distribution);
    initManipulationTechniquesChart(chartData?.manipulation_techniques);
    initKnowledgeUsageChart(chartData?.knowledge_usage);
}

/* Initialize spam vs ham chart */
function initSpamVsHamChart(data) {
    const ctx = document.getElementById('chart-spam-vs-ham');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Spam', 'Ham'],
            datasets: [{
                label: 'Distribution',
                data: [data?.spam_count || 0, data?.ham_count || 0],
                backgroundColor: [
                    'rgba(239, 68, 68, 0.5)',
                    'rgba(34, 197, 94, 0.5)'
                ],
                borderColor: [
                    'rgba(239, 68, 68, 1)',
                    'rgba(34, 197, 94, 1)'
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

/* Initialize risk distribution chart */
function initRiskDistributionChart(data) {
    const ctx = document.getElementById('chart-risk-distribution');
    if (!ctx) return;
    
    const riskLevels = ['Very Low', 'Low', 'Medium', 'High', 'Critical'];
    const counts = riskLevels.map(level => data?.risk_counts[level] || 0);
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
                }
            }
        }
    });
}

/* Initialize confidence distribution chart */
function initConfidenceDistributionChart(data) {
    const ctx = document.getElementById('chart-confidence-distribution');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'],
            datasets: [{
                label: 'Distribution',
                data: [10, 15, 25, 30, 30], // Default data
                backgroundColor: [
                    'rgba(107, 114, 128, 0.5)',
                    'rgba(161, 167, 182, 0.5)',
                    'rgba(212, 209, 214, 0.5)',
                    'rgba(185, 242, 255, 0.5)',
                    'rgba(34, 197, 94, 0.5)'
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

/* Initialize model confidence over time chart */
function initModelConfidenceOverTimeChart(data) {
    const ctx = document.getElementById('chart-model-confidence');
    if (!ctx) return;
    
    const labels = data?.labels || ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 5', 'Day 7'];
    const values = data?.values || [0.72, 0.75, 0.68, 0.81, 0.74, 0.79, 0.83];
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Model Confidence',
                data: values,
                backgroundColor: 'rgba(34, 197, 94, 0.2)',
                borderColor: 'rgba(34, 197, 94, 1)',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

/* Initialize message type chart */
function initMessageTypeChart(data) {
    const ctx = document.getElementById('chart-message-type');
    if (!ctx) return;
    
    const labels = Object.keys(data?.type_counts || {});
    const counts = Object.values(data?.type_counts || {});
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Message Count',
                data: counts,
                backgroundColor: typeColors(labels),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

/* Initialize manipulation techniques chart */
function initManipulationTechniquesChart(data) {
    const ctx = document.getElementById('chart-manipulation-techniques');
    if (!ctx) return;
    
    const labels = data?.labels || ['Urgency', 'Authority', 'Fear', 'Greed', 'Trust'];
    const values = data?.values || [38, 25, 20, 12, 5];
    const colors = [
        'rgba(245, 158, 11, 0.5)',
        'rgba(239, 68, 68, 0.5)',
        'rgba(139, 92, 246, 0.5)',
        'rgba(251, 191, 36, 0.5)',
        'rgba(34, 197, 94, 0.5)'
    ];
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                label: 'Techniques',
                data: values,
                backgroundColor: colors,
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

/* Initialize knowledge usage chart */
function initKnowledgeUsageChart(data) {
    const ctx = document.getElementById('chart-knowledge-usage');
    if (!ctx) return;
    
    const labels = data?.labels || ['Phishing', 'Malware', 'Spam', 'Scams', 'Other'];
    const values = data?.values || [42, 28, 35, 18, 12];
    const colors = [
        'rgba(34, 197, 94, 0.5)',
        'rgba(34, 197, 94, 0.5)',
        'rgba(34, 197, 94, 0.5)',
        'rgba(239, 68, 68, 0.5)',
        'rgba(107, 114, 128, 0.5)'
    ];
    const borderColors = [
        'rgba(34, 197, 94, 1)',
        'rgba(34, 197, 94, 1)',
        'rgba(34, 197, 94, 1)',
        'rgba(239, 68, 68, 1)',
        'rgba(107, 114, 128, 1)'
    ];
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Usage Count',
                data: values,
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