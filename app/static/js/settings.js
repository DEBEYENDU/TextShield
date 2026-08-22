/* TextShield Settings JavaScript - Settings Page */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize settings on load
    initSettings();
    
    // Initialize range sliders
    initRangeSliders();
    
    // Initialize theme toggle
    initThemeToggle();
});

/* Initialize settings */
function initSettings() {
    // Load current settings from API
    fetch('/api/settings')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadSettings(data.data);
            }
        })
        .catch(error => {
            console.error('Failed to fetch settings:', error);
        });
}

/* Load current settings */
function loadSettings(settings) {
    // Load theme
    const themeRadios = document.querySelectorAll('input[name="theme"]');
    themeRadios.forEach(radio => {
        if (radio.value === settings.theme) {
            radio.checked = true;
        }
    });
    
    // Load LLM provider
    const llmSelect = document.getElementById('llm-provider');
    if (llmSelect) {
        llmSelect.value = settings.llm_provider || 'ollama';
    }
    
    // Load embedding model
    const embeddingSelect = document.getElementById('embedding-model');
    if (embeddingSelect) {
        embeddingSelect.value = settings.embedding_model || 'sentence-transformers/all-MiniLM-L6-v2';
    }
    
    // Load confidence thresholds
    const thresholdData = settings.confidence_thresholds;
    if (thresholdData) {
        if (document.getElementById('spam-threshold')) {
            document.getElementById('spam-threshold').value = thresholdData.spam_threshold || 0.5;
            document.getElementById('spam-threshold-value').innerText = thresholdData.spam_threshold || 0.5;
        }
        if (document.getElementById('risk-threshold')) {
            document.getElementById('risk-threshold').value = thresholdData.risk_threshold || 0.3;
            document.getElementById('risk-threshold-value').innerText = thresholdData.risk_threshold || 0.3;
        }
    }
    
    // Load decision thresholds
    const decisionThresholds = settings.decision_thresholds;
    if (decisionThresholds) {
        if (document.getElementById('high-confidence')) {
            document.getElementById('high-confidence').value = decisionThresholds.high_confidence || 0.7;
            document.getElementById('high-confidence-value').innerText = decisionThresholds.high_confidence || 0.7;
        }
        if (document.getElementById('medium-confidence')) {
            document.getElementById('medium-confidence').value = decisionThresholds.medium_confidence || 0.4;
            document.getElementById('medium-confidence-value').innerText = decisionThresholds.medium_confidence || 0.4;
        }
    }
})

/* Initialize range sliders */
function initRangeSliders() {
    const sliders = document.querySelectorAll('input[type="range"]');
    
    sliders.forEach(slider => {
        slider.addEventListener('input', function() {
            const valueDisplay = document.getElementById(this.id + '-value');
            if (valueDisplay) {
                valueDisplay.innerText = this.value;
            }
        });
    });
}

/* Initialize theme toggle */
function initThemeToggle() {
    const themeRadios = document.querySelectorAll('input[name="theme"]');
    
    themeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            const selectedTheme = this.value;
            
            // Update root CSS variables
            if (selectedTheme === 'dark') {
                document.documentElement.style.setProperty('--primary', '#1d1e21');
                document.documentElement.style.setProperty('--primary-light', '#2d2f34');
                document.documentElement.style.setProperty('--accent', '#22d3ee');
                document.documentElement.style.setProperty('--text-primary', '#f8fafc');
                document.documentElement.style.setProperty('--text-secondary', '#64748b');
                document.documentElement.style.setProperty('--border', '#e2e8f0');
                document.documentElement.style.setProperty('--bg-gradient', 'linear-gradient(135deg, #0f0f23, #1a1a2e)');
            } else {
                document.documentElement.style.setProperty('--primary', '#f8fafc');
                document.documentElement.style.setProperty('--primary-light', '#ffffff');
                document.documentElement.style.setProperty('--accent', '#059669');
                document.documentElement.style.setProperty('--text-primary', '#1e293b');
                document.documentElement.style.setProperty('--text-secondary', '#64748b');
                document.documentElement.style.setProperty('--border', '#e2e8f0');
                document.documentElement.style.setProperty('--bg-gradient', 'linear-gradient(135deg, #ffffff, #f1f5f9)');
            }
            
            // Show toast
            showToast('Theme updated to ' + selectedTheme);
        });
    });
}

/* Save settings */
function saveSettings() {
    const form = document.getElementById('settings-form');
    if (!form) return;
    
    const formData = {
        theme: document.querySelector('input[name="theme"]:checked')?.value || 'light',
        llm_provider: document.getElementById('llm-provider')?.value || 'ollama',
        embedding_model: document.getElementById('embedding-model')?.value || 'sentence-transformers/all-MiniLM-L6-v2',
        confidence_thresholds: {
            spam_threshold: parseFloat(document.getElementById('spam-threshold')?.value || '0.5'),
            risk_threshold: parseFloat(document.getElementById('risk-threshold')?.value || '0.3')
        },
        decision_thresholds: {
            high_confidence: parseFloat(document.getElementById('high-confidence')?.value || '0.7'),
            medium_confidence: parseFloat(document.getElementById('medium-confidence')?.value || '0.4')
        }
    };
    
    fetch('/api/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Settings saved successfully');
        } else {
            showToast('Failed to save settings: ' + (data.error || ''));
        }
    })
    .catch(error => {
        console.error('Failed to save settings:', error);
        showToast('Network error while saving settings');
    });
}

/* Reset settings */
function resetSettings() {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
        // In a real implementation, this would reset to default settings
        showToast('Settings reset initiated');
    }
}