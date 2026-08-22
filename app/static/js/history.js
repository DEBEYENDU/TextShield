/* TextShield History JavaScript - Analysis History Page */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize history on load
    initHistory();
    
    // Initialize data tables
    initDataTable();
});

/* Initialize history */
function initHistory() {
    fetch('/api/history')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayHistory(data.data);
                updateHistoryStats(data.stats);
            }
        })
        .catch(error => {
            console.error('Failed to fetch history:', error);
        });
}

/* Display history table */
function displayHistory(analyses) {
    const tableBody = document.getElementById('history-table-body');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    analyses.forEach((analysis, index) => {
        const tr = document.createElement('tr');
        const riskClass = analysis.risk_level.toLowerCase().replace(' ', '-');
        
        tr.innerHTML = `
            <td>${analysis.date || 'N/A'}</td>
            <td>${analysis.message_type || 'N/A'}</td>
            <td>
                <span class="risk-badge risk-${riskClass}">${analysis.classification}</span>
            </td>
            <td><span class="risk-badge risk-${riskClass}">${analysis.risk_level}</span></td>
            <td>${(analysis.confidence * 100).toFixed(1)}%</td>
            <td>
                <button class="btn btn-sm btn-outline" onclick="reanalyze('${analysis.id}')">Reanalyze</button>
                <button class="btn btn-sm btn-outline text-danger" onclick="deleteAnalysis('${analysis.id}')">Delete</button>
            </td>
        `;
        tableBody.appendChild(tr);
    });
}

/* Update history stats */
function updateHistoryStats(stats) {
    const statsEl = document.getElementById('history-stats');
    if (!statsEl) return;
    
    statsEl.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${stats.total || 0}</div>
            <div class="stat-label">Total Analyzed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value stat-red">${stats.spam || 0}</div>
            <div class="stat-label">Spam</div>
        </div>
        <div class="stat-card">
            <div class="stat-value stat-green">${stats.ham || 0}</div>
            <div class="stat-label">Ham</div>
        </div>
    `;
}

/* Export history */
function exportHistory() {
    // In a real implementation, this would export the history data
    showToast('History export initiated');
}

/* Delete selected analysis */
function deleteAnalysis(id) {
    if (confirm('Are you sure you want to delete this analysis?')) {
        fetch(`/api/analysis/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Analysis deleted');
                initHistory(); // Refresh
            }
        })
        .catch(error => {
            console.error('Failed to delete analysis:', error);
        });
}

/* Delete selected multiple */
function deleteSelected() {
    // In a real implementation, this would delete selected items
    showToast('Delete selected initiated');
}

/* Reanalyze selected */
function reanalyzeSelected() {
    // In a real implementation, this would reanalyze selected items
    showToast('Reanalyze selected initiated');
}

/* Reanalyze single */
function reanalyze(id) {
    if (confirm('Are you sure you want to reanalyze this message?')) {
        window.location.href = `/analyze?id=${id}`;
    }
}

/* Initialize DataTable */
function initDataTable() {
    // In a real implementation, this would initialize DataTables.js
    // For now, just make the table responsive
    const table = document.querySelector('#history-table');
    if (table) {
        table.classList.add('table-responsive');
    }
}