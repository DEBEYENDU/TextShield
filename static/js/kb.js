/* TextShield - knowledge base page logic */
(() => {
    "use strict";

    const statusEl = document.getElementById("kb-status");
    const rebuildBtn = document.getElementById("rebuild-btn");
    const resultEl = document.getElementById("rebuild-result");

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    }

    function renderStatus(data) {
        statusEl.innerHTML = `
            <div class="kpi">
                <div><span class="tag ${data.ready ? "on" : "off"}">${data.ready ? "READY" : "NOT BUILT"}</span></div>
                <div class="kpi-value">${data.chunk_count}</div>
                <div class="kpi-label">knowledge chunks</div>
            </div>
            <div class="kpi">
                <div class="kpi-value">${data.document_count}</div>
                <div class="kpi-label">documents indexed</div>
            </div>
            <div class="kpi">
                <div class="kpi-value" style="font-size:1.05rem;">${escapeHtml(data.backend)}</div>
                <div class="kpi-label">vector db backend</div>
            </div>
            <div class="kpi">
                <div class="kpi-value" style="font-size:1.05rem;">${escapeHtml(data.embedding_provider)}</div>
                <div class="kpi-label">embedding provider</div>
            </div>
            <div class="kpi">
                <div class="kpi-value" style="font-size:1rem;">${data.built_at ? escapeHtml(new Date(data.built_at).toLocaleString()) : "-"}</div>
                <div class="kpi-label">last built</div>
            </div>
            <div class="mt">
                <div class="kpi-label" style="margin-bottom:0.5rem;">Categories</div>
                <div class="tag-list">${(data.categories || []).map((c) => `<span class="tag">${escapeHtml(c)}</span>`).join("")}</div>
            </div>`;
    }

    rebuildBtn.addEventListener("click", async () => {
        rebuildBtn.disabled = true;
        rebuildBtn.innerHTML = '<span class="spinner"></span> Rebuilding...';
        resultEl.innerHTML = "";
        try {
            const response = await fetch("/api/knowledge-base/rebuild", { method: "POST" });
            const payload = await response.json();
            if (!response.ok) {
                resultEl.innerHTML = `<div class="alert alert-error">${escapeHtml(payload.detail || "Rebuild failed.")}</div>`;
            } else {
                resultEl.innerHTML = `<div class="alert alert-info">Knowledge base rebuilt: ${payload.chunk_count} chunks from ${payload.document_count} documents.</div>`;
                renderStatus(payload);
            }
        } catch (error) {
            resultEl.innerHTML = `<div class="alert alert-error">Network error while rebuilding.</div>`;
        } finally {
            rebuildBtn.disabled = false;
            rebuildBtn.textContent = "Rebuild knowledge base";
        }
    });

    fetch("/api/knowledge-base")
        .then((r) => r.json())
        .then(renderStatus)
        .catch(() => {
            statusEl.innerHTML = `<div class="alert alert-error">Could not load knowledge base status.</div>`;
        });
})();