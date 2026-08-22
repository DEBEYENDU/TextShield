/* TextShield Chart Initialization */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all charts when page loads
    initRiskChart();
    initSpamHamChart();
    initConfidenceChart();
    initModelConfidenceChart();
    initMessageTypeChart();
    initManipulationTechniquesChart();
    initKnowledgeUsageChart();
});

function initRiskChart() {
    const ctx = document.getElementById('chart-risk');
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
            }
        }
    });
}

function initSpamHamChart() {
    const ctx = document.getElementById('chart-spam-vs-ham');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Spam', 'Ham'],
            datasets: [{
                label: 'Distribution',
                data: [45, 55],
                backgroundColor: ['rgba(239, 68, 68, 0.5)', 'rgba(34, 197, 94, 0.5)'],
                borderColor: ['rgba(239, 68, 68, 1)', 'rgba(34, 197, 94, 1)'],
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

function initConfidenceChart() {
    const ctx = document.getElementById('chart-confidence-distribution');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'],
            datasets: [{
                label: 'Confidence Distribution',
                data: [15, 25, 30, 20, 10],
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

function initModelConfidenceChart() {
    const ctx = document.getElementById('chart-model-confidence');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
            datasets: [{
                label: 'Model Confidence',
                data: [0.72, 0.75, 0.68, 0.81, 0.74, 0.79, 0.83],
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
                },
                tooltip: {
                    backgroundColor: 'var(--primary)',
                    titleColor: '#f8fafc',
                    bodyColor: '#e2e8f0'
                }
            }
        }
    });
}

function initMessageTypeChart() {
    const ctx = document.getElementById('chart-message-type');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['SMS', 'Email', 'Text', 'Other'],
            datasets: [{
                label: 'Message Count',
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
                    display: false
                }
            }
        }
    });
}

function initManipulationTechniquesChart() {
    const ctx = document.getElementById('chart-manipulation-techniques');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Urgency', 'Authority', 'Fear', 'Greed', 'Trust'],
            datasets: [{
                label: 'Techniques',
                data: [38, 25, 20, 12, 5],
                backgroundColor: [
                    'rgba(245, 158, 11, 0.5)',
                    'rgba(239, 68, 68, 0.5)',
                    'rgba(139, 92, 246, 0.5)',
                    'rgba(251, 191, 36, 0.5)',
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

function initKnowledgeUsageChart() {
    const ctx = document.getElementById('chart-knowledge-usage');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Phishing', 'Malware', 'Spam', 'Scams', 'Other'],
            datasets: [{
                label: 'Usage Count',
                data: [42, 28, 35, 18, 12],
                backgroundColor: [
                    'rgba(34, 197, 94, 0.5)',
                    'rgba(34, 197, 94, 0.5)',
                    'rgba(34, 197, 94, 0.5)',
                    'rgba(239, 68, 68, 0.5)',
                    'rgba(107, 114, 128, 0.5)'
                ],
                borderColor: [
                    'rgba(34, 197, 94, 1)',
                    'rgba(34, 197, 94, 1)',
                    'rgba(34, 197, 94, 1)',
                    'rgba(239, 68, 68, 1)',
                    'rgba(107, 114, 128, 1)'
                ],
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