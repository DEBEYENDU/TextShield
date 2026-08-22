/* TextShield Evidence JavaScript - Evidence Viewer Page */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize evidence viewer on load
    initEvidenceViewer();
});

/* Initialize evidence viewer */
function initEvidenceViewer() {
    // Fetch evidence data via AJAX
    fetch('/api/evidence')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayEvidence(data.data);
            }
        })
        .catch(error => {
            console.error('Failed to fetch evidence:', error);
        });
}

/* Display evidence data */
function displayEvidence(data) {
    const evidenceCountEl = document.getElementById('evidence-count');
    const avgSimilarityEl = document.getElementById('avg-similarity');
    const evidenceTableBody = document.getElementById('evidence-table-body');
    
    if (evidenceCountEl) {
        evidenceCountEl.innerText = data.total_documents || 0;
    }
    if (avgSimilarityEl) {
        avgSimilarityEl.innerText = data.average_similarity ? (data.average_similarity * 100).toFixed(1) + '%' : '0%';
    }
    
    if (evidenceTableBody && data.documents) {
        evidenceTableBody.innerHTML = '';
        
        data.documents.forEach((doc, index) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <div class="chip">${doc.title || 'Document ' + (index + 1)}</div>
                    <small>${doc.source || 'Unknown'}</small>
                </div>
                <td>${doc.category || 'Uncategorized'}</td>
                <td>
                    <span class="risk-badge risk-${doc.trust_level || 'low'}">${doc.trust_level || 'Low'}</span>
                </td>
                <td>${(doc.similarity || 0) * 100}%</td>
                <td>${doc.highlighted_evidence || 'No highlighted evidence'}</td>
            `;
            evidenceTableBody.appendChild(tr);
        });
    }
}

/* Close evidence viewer */
function closeEvidenceViewer() {
    // In a real implementation, this would close a modal or navigate away
    window.history.back();
}