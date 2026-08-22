/* TextShield System JavaScript - System Health Page */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize system health on load
    initSystemHealth();
    
    // Start health polling
    startHealthPolling();
});

/* Initialize system health */
function initSystemHealth() {
    // Initial fetch of all system status
    fetchHealthStatus();
}

/* Fetch health status */
function fetchHealthStatus() {
    fetch('/api/system-health')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayHealthStatus(data.data);
            }
        })
        .catch(error => {
            console.error('Failed to fetch health status:', error);
        });
}

/* Display health status */
function displayHealthStatus(data) {
    // Model status
    const modelStatus = document.getElementById('model-status');
    const modelName = document.getElementById('model-name');
    const modelAccuracy = document.getElementById('model-accuracy');
    const modelLastUpdate = document.getElementById('model-last-update');
    
    if (modelStatus) {
        modelStatus.innerHTML = data.model.status === 'healthy' 
            ? `<span class="status-dot"></span> Healthy` 
            : `<span class="status-dot error"></span> Unhealthy`;
        if (modelName) modelName.innerText = data.model.name || 'Unknown';
        if (modelAccuracy) modelAccuracy.innerText = data.model.accuracy ? (data.model.accuracy * 100).toFixed(1) + '%' : 'N/A';
        if (modelLastUpdate) modelLastUpdate.innerText = data.model.last_updated ? new Date(data.model.last_updated).toLocaleString() : 'Never';
    }
    
    // LLM status
    const llmStatus = document.getElementById('llm-status');
    const llmName = document.getElementById('llm-name');
    const llmModel = document.getElementById('llm-model');
    const llmLastUpdate = document.getElementById('llm-last-update');
    
    if (llmStatus) {
        const llmData = data.llm;
        llmStatus.innerHTML = llmData.status === 'healthy' 
            ? `<span class="status-dot"></span> Healthy` 
            : `<span class="status-dot error"></span> Unhealthy`;
        if (llmName) llmName.innerText = llmData.provider || 'Unknown';
        if (llmModel) llmModel.innerText = llmData.model || 'N/A';
        if (llmLastUpdate) llmLastUpdate.innerText = llmData.last_updated ? new Date(llmData.last_updated).toLocaleString() : 'Never';
    }
    
    // Vector database status
    const vectorStatus = document.getElementById('vector-status');
    const vectorCount = document.getElementById('vector-count');
    const vectorIndexSize = document.getElementById('vector-index-size');
    const vectorLastUpdate = document.getElementById('vector-last-update');
    
    if (vectorStatus) {
        const vectorData = data.vector_db;
        vectorStatus.innerHTML = vectorData.status === 'healthy' 
            ? `<span class="status-dot"></span> Healthy` 
            : `<span class="status-dot error"></span> Unhealthy`;
        if (vectorCount) vectorCount.innerText = vectorData.document_count || '0';
        if (vectorIndexSize) vectorIndexSize.innerText = vectorData.index_size || 'N/A';
        if (vectorLastUpdate) vectorLastUpdate.innerText = vectorData.last_updated ? new Date(vectorData.last_updated).toLocaleString() : 'Never';
    }
    
    // Knowledge base status
    const kbStatus = document.getElementById('kb-status');
    const kbCount = document.getElementById('kb-count');
    const kbLastUpdate = document.getElementById('kb-last-update');
    
    if (kbStatus) {
        const kbData = data.knowledge_base;
        kbStatus.innerHTML = kbData.status === 'healthy' 
            ? `<span class="status-dot"></span> Healthy` 
            : `<span class="status-dot error"></span> Unhealthy`;
        if (kbCount) kbCount.innerText = kbData.document_count || '0';
        if (kbLastUpdate) kbLastUpdate.innerText = kbData.last_updated ? new Date(kbData.last_updated).toLocaleString() : 'Never';
    }
    
    // Database status
    const dbStatus = document.getElementById('db-status');
    const dbType = document.getElementById('db-type');
    const dbConnections = document.getElementById('db-connections');
    const dbLastUpdate = document.getElementById('db-last-update');
    
    if (dbStatus) {
        const dbData = data.database;
        dbStatus.innerHTML = dbData.status === 'healthy' 
            ? `<span class="status-dot"></span> Healthy` 
            : `<span class="status-dot error"></span> Unhealthy`;
        if (dbType) dbType.innerText = dbData.type || 'Unknown';
        if (dbConnections) dbConnections.innerText = dbData.active_connections || '0';
        if (dbLastUpdate) dbLastUpdate.innerText = dbData.last_updated ? new Date(dbData.last_updated).toLocaleString() : 'Never';
    }
    
    // API health
    const apiStatus = document.getElementById('api-status');
    const apiResponseTime = document.getElementById('api-response-time');
    const apiLastUpdate = document.getElementById('api-last-update');
    
    if (apiStatus) {
        const apiData = data.api;
        apiStatus.innerHTML = apiData.status === 'healthy' 
            ? `<span class="status-dot"></span> Healthy` 
            : `<span class="status-dot error"></span> Unhealthy`;
        if (apiResponseTime) apiResponseTime.innerText = apiData.avg_response_time ? apiData.avg_response_time + 'ms' : 'N/A';
        if (apiLastUpdate) apiLastUpdate.innerText = apiData.last_updated ? new Date(apiData.last_updated).toLocaleString() : 'Never';
    }
    
    // App version and resources
    const appVersion = document.getElementById('app-version');
    const memoryUsage = document.getElementById('memory-usage');
    const storageSize = document.getElementById('storage-size');
    
    if (appVersion) appVersion.innerText = data.version || 'Unknown';
    if (memoryUsage) memoryUsage.innerText = data.memory_usage ? (data.memory_usage / 1024 / 1024).toFixed(1) + ' MB' : 'N/A';
    if (storageSize) storageSize.innerText = data.storage_size ? (data.storage_size / 1024 / 1024 / 1024).toFixed(2) + ' GB' : 'N/A';
}

/* Start health polling */
function startHealthPolling() {
    // Fetch health status every 30 seconds
    setInterval(fetchHealthStatus, 30000);
    // Initial fetch
    fetchHealthStatus();
}