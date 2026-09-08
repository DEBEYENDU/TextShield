/* TextShield - about page: model information */
(() => {
    "use strict";

    const _ts = window.textshield || window.TextShield || window.App || {};
    if (!window.textshield) {
        console.warn("[TextShield] common.js not loaded before about.js - using fallback");
        window.textshield = _ts;
    }
    const escapeHtml = (_ts && _ts.escapeHtml) || function (v) {
        return String(v ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    };
    const errorHandler = (_ts && _ts.errorHandler) || console.error;

    const body = document.getElementById("model-body");
    if (!body) return;

    function renderModel(data) {
        try {
            if (!data.available) {
                body.innerHTML = `<p class="muted">${escapeHtml(data.message || "Model not trained yet.")}</p>`;
                return;
            }
            const metrics = data.metrics || {};
            const comparison = data.comparison || {};
            const rows = Object.entries(comparison).map(([name, entry]) => {
                const m = entry.metrics || {};
                return `<tr>
                    <td>${escapeHtml(name)}</td>
                    <td class="num">${escapeHtml(m.accuracy ?? "-")}</td>
                    <td class="num">${escapeHtml(m.precision_spam ?? "-")}</td>
                    <td class="num">${escapeHtml(m.recall_spam ?? "-")}</td>
                    <td class="num"><b>${escapeHtml(m.f1_spam ?? "-")}</b></td>
                </tr>`;
            }).join("");

            body.innerHTML = `
                <table class="data">
                    <tbody>
                        <tr><td>Algorithm</td><td class="num"><b>${escapeHtml(data.algorithm)}</b></td></tr>
                        <tr><td>Trained at</td><td class="num">${escapeHtml(data.trained_at ? new Date(data.trained_at).toLocaleString() : "-")}</td></tr>
                        <tr><td>Training rows</td><td class="num">${escapeHtml(data.dataset ? data.dataset.train_rows : "-")}</td></tr>
                        <tr><td>Test rows</td><td class="num">${escapeHtml(data.dataset ? data.dataset.test_rows : "-")}</td></tr>
                        <tr><td>Accuracy (test set)</td><td class="num">${escapeHtml(metrics.accuracy ?? "-")}</td></tr>
                        <tr><td>Precision (spam)</td><td class="num">${escapeHtml(metrics.precision_spam ?? "-")}</td></tr>
                        <tr><td>Recall (spam)</td><td class="num">${escapeHtml(metrics.recall_spam ?? "-")}</td></tr>
                        <tr><td>F1 (spam)</td><td class="num"><b>${escapeHtml(metrics.f1_spam ?? "-")}</b></td></tr>
                        <tr><td>Label mapping</td><td class="num">${escapeHtml(JSON.stringify(data.label_mapping || {}))}</td></tr>
                    </tbody>
                </table>
                <h2 class="mt">Model comparison (held-out test set)</h2>
                <table class="data">
                    <thead><tr><th>Algorithm</th><th class="num">Accuracy</th><th class="num">Precision (spam)</th><th class="num">Recall (spam)</th><th class="num">F1 (spam)</th></tr></thead>
                    <tbody>${rows}</tbody>
                </table>`;
        } catch (e) {
            errorHandler(e);
        }
    }

    fetch("/api/model-info")
        .then((r) => r.json().catch(() => ({})))
        .then(renderModel)
        .catch((e) => {
            errorHandler(e);
            body.innerHTML = `<p class="muted">Could not load model information.</p>`;
        });
})();
