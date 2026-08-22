/* TextShield Index JavaScript - Analyze Message Page */

document.addEventListener('DOMContentLoaded', function() {
    // Tab switching
    initTabs();
    
    // Analyze form submission
    initAnalyzeForm();
    
    // Cancel button
    initCancelButton();
});

/* Initialize tab switching */
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Update active tab button
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Update active tab panel
            const tabName = this.getAttribute('data-tab');
            tabPanels.forEach(panel => {
                panel.classList.remove('active');
                if (panel.getAttribute('data-panel') === tabName) {
                    panel.classList.add('active');
                }
            });
        });
    });
}

/* Initialize analyze form submission */
function initAnalyzeForm() {
    const form = document.getElementById('analyze-form');
    const analyzeBtn = document.getElementById('analyze-btn');
    const resultArea = document.getElementById('result-area');
    const errorArea = document.getElementById('error-area');
    const loadingArea = document.getElementById('loading-area');
    
    if (!form || !analyzeBtn) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get the selected tab value
        const activeTab = document.querySelector('.tab-btn.active');
        const tabName = activeTab ? activeTab.getAttribute('data-tab') : 'text';
        
        // Get message based on tab
        let message = '';
        let subject = '';
        let sender = '';
        
        if (tabName === 'sms') {
            message = document.getElementById('sms-message').value;
        } else if (tabName === 'text') {
            message = document.getElementById('text-message').value;
        } else if (tabName === 'email') {
            subject = document.getElementById('email-subject').value;
            sender = document.getElementById('email-sender').value;
            message = document.getElementById('email-body').value;
        }
        
        // Show loading, hide results/errors
        showLoading(true);
        hideElement(resultArea);
        hideElement(errorArea);
        analyzeBtn.disabled = true;
        analyzeBtn.innerText = 'Analyzing...';
        
        // Send to API
        fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                input_type: tabName,
                message: message,
                subject: subject,
                sender: sender
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showResults(data.data);
            } else {
                showError(data.error || 'Analysis failed');
            }
        })
        .catch(error => {
            console.error('Analysis error:', error);
            showError('Network error or server unavailable');
        })
        .finally(() => {
            showLoading(false);
            analyzeBtn.disabled = false;
            analyzeBtn.innerText = 'Analyze Message';
        });
    });
}

/* Initialize cancel button */
function initCancelButton() {
    const cancelBtn = document.getElementById('cancel-btn');
    if (!cancelBtn) return;
    
    cancelBtn.addEventListener('click', function() {
        window.history.back();
    });
}

/* Show loading state */
function showLoading(show) {
    const loadingArea = document.getElementById('loading-area');
    const resultArea = document.getElementById('result-area');
    const errorArea = document.getElementById('error-area');
    const analyzeBtn = document.getElementById('analyze-btn');
    
    if (show) {
        loadingArea.classList.remove('hidden');
        resultArea.classList.add('hidden');
        errorArea.classList.add('hidden');
    } else {
        loadingArea.classList.add('hidden');
    }
}

/* Hide element */
function hideElement(el) {
    if (el) el.classList.add('hidden');
}

/* Show results */
function showResults(data) {
    const resultArea = document.getElementById('result-area');
    const classification = data.classification.toLowerCase();
    
    resultArea.classList.remove('hidden');
    resultArea.classList.add(classification);
    resultArea.innerHTML = `
        <div class="risk-badge" style="color: ${classification === 'spam' ? 'var(--error)' : 'var(--success)'}">
            ${data.classification}
        </div>
        <p id="classification-text" style="margin-top: 0.5rem; font-size: 1.25rem; font-weight: 600;">
            ${data.classification}
        </p>
        <p>Confidence: <span id="confidence-value">${(data.confidence * 100).toFixed(1)}%</span></p>
        <p>Risk Level: <span id="risk-level-badge" class="risk-badge risk-${data.risk_level.toLowerCase()}">${data.risk_level}</span></p>
    `;
    
    // Populate additional details
    const summaryEl = document.createElement('p');
    summaryEl.innerHTML = `
        <strong>Summary:</strong> ${data.explanation || 'No summary available'}<br>
        <strong>Risk Factors:</strong> ${data.risk_factors ? data.risk_factors.join(', ') : 'None detected'}
    `;
    resultArea.appendChild(summaryEl);
    
    // Show evidence
    if (data.rag_evidence && data.rag_evidence.length > 0) {
        const evidenceEl = document.createElement('div');
        evidenceEl.innerHTML = '<h4>Supporting Evidence</h4><ul>';
        data.rag_evidence.forEach(ev => {
            evidenceEl.innerHTML += `<li>${ev.content || 'No content'} <span style="font-size: 0.75rem; color: var(--text-secondary);">(similarity: ${(ev.similarity || 0) * 100}%)</span></li>`;
        });
        evidenceEl.innerHTML += '</ul>';
        resultArea.appendChild(evidenceEl);
    }
    
    // Show recommendations
    if (data.recommended_action) {
        const recEl = document.createElement('div');
        recEl.innerHTML = `<div class="mt-2"><strong>Recommendation:</strong> ${data.recommended_action}</div>`;
        resultArea.appendChild(recEl);
    }
    
    // Show original message snippet
    const msgEl = document.createElement('p');
    msgEl.style.marginTop = '1rem';
    msgEl.style.fontStyle = 'italic';
    msgEl.innerText = data.original_message ? 'Message: ' + data.original_message.substring(0, 100) + (data.original_message.length > 100 ? '...' : '') : 'No message captured';
    resultArea.appendChild(msgEl);
    
    // Make visible
    resultArea.classList.add('visible');
}

/* Show error */
function showError(message) {
    const errorArea = document.getElementById('error-area');
    const resultArea = document.getElementById('result-area');
    
    errorArea.querySelector('p').innerText = message;
    errorArea.classList.remove('hidden');
    resultArea.classList.add('hidden');
}