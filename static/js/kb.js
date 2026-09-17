/* TextShield - knowledge base page logic */
(() => {
    "use strict";

    // Defensive namespace initialization - works even if common.js failed or loaded late
    const _ts = window.textshield || window.TextShield || window.App || {};
    if (!window.textshield) {
        console.warn("[TextShield] common.js not loaded before kb.js - using fallback");
        window.textshield = _ts;
    }
    const escapeHtml = (_ts && _ts.escapeHtml) || function (v) {
        return String(v ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    };
    const apiRequest = (_ts && (_ts.apiRequest || _ts.fetchJson)) || fetch;
    const showToast = (_ts && _ts.showToast) || function (m) { console.log("[toast]", m); };
    const errorHandler = (_ts && _ts.errorHandler) || function (e) { console.error(e); };

    const statusEl = document.getElementById("kb-status");
    const rebuildBtn = document.getElementById("rebuild-btn");
    const resultEl = document.getElementById("rebuild-result");

    // If not on KB page, do nothing
    if (!statusEl && !rebuildBtn) return;

    function renderStatus(data) {
        if (!statusEl) return;
        try {
            statusEl.innerHTML = `
                <div class="kpi">
                    <div><span class="tag ${data.ready ? "on" : "off"}">${data.ready ? "READY" : "NOT BUILT"}</span></div>
                    <div class="kpi-value">${data.chunk_count ?? "-"}</div>
                    <div class="kpi-label">knowledge chunks</div>
                </div>
                <div class="kpi">
                    <div class="kpi-value">${data.document_count ?? "-"}</div>
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
        } catch (e) {
            errorHandler(e);
        }
    }

    if (rebuildBtn) {
        rebuildBtn.addEventListener("click", async () => {
            if (!rebuildBtn || !resultEl) return;
            rebuildBtn.disabled = true;
            rebuildBtn.innerHTML = '<span class="spinner"></span> Rebuilding...';
            if (resultEl) resultEl.innerHTML = "";
            try {
                const response = await fetch("/api/knowledge-base/rebuild", { method: "POST" });
                const payload = await response.json().catch(() => ({}));
                if (!response.ok) {
                    if (resultEl) resultEl.innerHTML = `<div class="alert alert-error">${escapeHtml(payload.detail || "Rebuild failed.")}</div>`;
                } else {
                    if (resultEl) resultEl.innerHTML = `<div class="alert alert-info">Knowledge base rebuilt: ${payload.chunk_count} chunks from ${payload.document_count} documents.</div>`;
                    renderStatus(payload);
                    showToast("Knowledge base rebuilt", "info");
                }
            } catch (error) {
                errorHandler(error, "Network error while rebuilding.");
                if (resultEl) resultEl.innerHTML = `<div class="alert alert-error">Network error while rebuilding.</div>`;
            } finally {
                rebuildBtn.disabled = false;
                rebuildBtn.textContent = "Rebuild knowledge base";
            }
        });
    }

    // Initial load
    fetch("/api/knowledge-base")
        .then((r) => r.json())
        .then(renderStatus)
        .catch((e) => {
            errorHandler(e, "Could not load knowledge base status.");
            if (statusEl) statusEl.innerHTML = `<div class="alert alert-error">Could not load knowledge base status.</div>`;
        });
})();
