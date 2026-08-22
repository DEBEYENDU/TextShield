/* TextShield Results JavaScript - Analysis Results Page */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize results on load
    initResults();
    
    // Export functionality
    initExport();
});

/* Initialize results display */
function initResults() {
    // Get URL parameters or fetch from API
    const urlParams = new URLSearchParams(window.location.search);
    const messageId = urlParams.get('id');
    
    if (messageId) {
        fetch(`/api/analysis/${messageId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayResults(data.data);
                }
            })
            .catch(error => {
                console.error('Failed to fetch analysis:', error);
            });
    }
}

/* Display analysis results */
function displayResults(data) {
    // Set original message
    const originalMessageEl = document.getElementById('original-message');
    if (originalMessageEl) {
        originalMessageEl.innerText = data.original_message || 'No message available';
    }
    
    // Set classification
    const classificationBadge = document.getElementById('classification-badge');
    const classificationText = document.getElementById('classification-text');
    const confidenceValue = document.getElementById('confidence-value');
    const riskLevelBadge = document.getElementById('risk-level-badge');
    
    if (classificationBadge) {
        classificationBadge.innerText = data.classification;
        classificationBadge.className = `risk-badge risk-${data.classification.toLowerCase()}`;
    }
    if (classificationText) {
        classificationText.innerText = data.classification;
    }
    if (confidenceValue) {
        confidenceValue.innerText = (data.confidence * 100).toFixed(1) + '%';
    }
    if (riskLevelBadge) {
        riskLevelBadge.innerText = data.risk_level;
        riskLevelBadge.className = `risk-badge risk-${data.risk_level.toLowerCase()}`;
    }
    
    // Set summary
    const summaryEl = document.getElementById('summary-text');
    if (summaryEl) {
        summaryEl.innerHTML = data.summary || 'No summary available';
    }
    
    // Set reasoning
    const reasoningEl = document.getElementById('reasoning-text');
    if (reasoningEl) {
        reasoningEl.innerHTML = data.reasoning || 'No reasoning available';
    }
    
    // Set evidence
    const evidenceList = document.getElementById('evidence-list');
    if (evidenceList && data.evidence) {
        evidenceList.innerHTML = '';
        data.evidence.forEach((ev, index) => {
            const li = document.createElement('div');
            li.className = 'mb-2 p-2 rounded';
            li.style.background = 'var(--primary-light)';
            li.style.marginBottom = '0.5rem';
            li.style.padding = '0.5rem';
            li.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">Evidence ${index + 1}</h6>
                    <small>${ev.source || 'Unknown'}</small>
                </div>
                <p class="mb-1">${ev.content || 'No content available'}</p>
                <small>Similarity: ${(ev.similarity || 0) * 100}%</small>
            `;
            evidenceList.appendChild(li);
        });
    }
    
    // Set recommendations
    const recommendationsList = document.getElementById('recommendations-list');
    if (recommendationsList && data.recommendations) {
        recommendationsList.innerHTML = '';
        data.recommendations.forEach((rec, index) => {
            const li = document.createElement('div');
            li.className = 'mb-2 p-2 rounded';
            li.style.background = 'var(--primary-light)';
            li.style.marginBottom = '0.5rem';
            li.style.padding = '0.5rem';
            li.innerHTML = `
                <div>
                    <strong>Recommendation ${index + 1}:</strong> ${rec}
                </div>
            `;
            recommendationsList.appendChild(li);
        });
    }
}

/* Export results */
function exportResults() {
    const classification = document.getElementById('classification-badge')?.innerText || '';
    const confidence = document.getElementById('confidence-value')?.innerText || '0%';
    const riskLevel = document.getElementById('risk-level-badge')?.innerText || '';
    const summary = document.getElementById('summary-text')?.innerHTML || '';
    
    const exportData = {
        classification: classification,
        confidence: confidence,
        risk_level: riskLevel,
        summary: summary,
        timestamp: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `textshield-analysis-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
}