/* TextShield - about page: model information */
(() => {
    "use strict";

    const body = document.getElementById("model-body");

    const { escapeHtml } = window.textshield;

    function renderModel(data) {
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
                <td class="num">${m.accuracy ?? "-"}</td>
                <td class="num">${m.precision_spam ?? "-"}</td>
                <td class="num">${m.recall_spam ?? "-"}</td>
                <td class="num"><b>${m.f1_spam ?? "-"}</b></td>
            </tr>`;
        }).join("");

        body.innerHTML = `
            <table class="data">
                <tbody>
                    <tr><td>Algorithm</td><td class="num"><b>${escapeHtml(data.algorithm)}</b></td></tr>
                    <tr><td>Trained at</td><td class="num">${escapeHtml(data.trained_at ? new Date(data.trained_at).toLocaleString() : "-")}</td></tr>
                    <tr><td>Training rows</td><td class="num">${data.dataset ? data.dataset.train_rows : "-"}</td></tr>
                    <tr><td>Test rows</td><td class="num">${data.dataset ? data.dataset.test_rows : "-"}</td></tr>
                    <tr><td>Accuracy (test set)</td><td class="num">${metrics.accuracy ?? "-"}</td></tr>
                    <tr><td>Precision (spam)</td><td class="num">${metrics.precision_spam ?? "-"}</td></tr>
                    <tr><td>Recall (spam)</td><td class="num">${metrics.recall_spam ?? "-"}</td></tr>
                    <tr><td>F1 (spam)</td><td class="num"><b>${metrics.f1_spam ?? "-"}</b></td></tr>
                    <tr><td>Label mapping</td><td class="num">${escapeHtml(JSON.stringify(data.label_mapping))}</td></tr>
                </tbody>
            </table>
            <h2 class="mt">Model comparison (held-out test set)</h2>
            <table class="data">
                <thead><tr><th>Algorithm</th><th class="num">Accuracy</th><th class="num">Precision (spam)</th><th class="num">Recall (spam)</th><th class="num">F1 (spam)</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>`;
    }

    fetch("/api/model-info")
        .then((r) => r.json())
        .then(renderModel)
        .catch(() => {
            body.innerHTML = `<p class="muted">Could not load model information.</p>`;
        });
})();