/* TextShield - analytics page: stats + lightweight canvas charts */
(() => {
    "use strict";

    const _ts = window.textshield || window.TextShield || window.App || {};
    if (!window.textshield) {
        console.warn("[TextShield] common.js not loaded before analytics.js - using fallback");
        window.textshield = _ts;
    }
    const escapeHtml = (_ts && _ts.escapeHtml) || function (v) {
        return String(v ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    };
    const errorHandler = (_ts && _ts.errorHandler) || console.error;

    const COLORS = { HIGH: "#ef4444", MEDIUM: "#f59e0b", LOW: "#22c55e",
                     spam: "#ef4444", ham: "#22c55e", blue: "#3b82f6",
                     sms: "#22d3ee", text: "#3b82f6", email: "#8b5cf6" };

    function getCanvas(idList) {
        for (const id of idList) {
            const el = document.getElementById(id);
            if (el) return el;
        }
        return null;
    }

    function drawBars(canvas, labels, values, colors) {
        if (!canvas || !canvas.getContext) return;
        const ctx = canvas.getContext("2d");
        const dpr = window.devicePixelRatio || 1;
        const w = canvas.clientWidth || 400;
        const h = canvas.clientHeight || 240;
        canvas.width = w * dpr;
        canvas.height = h * dpr;
        ctx.scale(dpr, dpr);
        ctx.clearRect(0, 0, w, h);

        const max = Math.max(1, ...values);
        const padL = 34, padB = 26, padT = 12, padR = 8;
        const innerW = w - padL - padR;
        const innerH = h - padT - padB;
        const n = labels.length;
        const slot = n ? innerW / n : innerW;
        const barW = Math.min(46, slot * 0.55);

        ctx.strokeStyle = "rgba(148,163,255,0.12)";
        ctx.fillStyle = "#8fa1c8";
        ctx.font = "10px Segoe UI, sans-serif";
        for (let g = 0; g <= 4; g++) {
            const y = padT + innerH - (g / 4) * innerH;
            ctx.beginPath();
            ctx.moveTo(padL, y);
            ctx.lineTo(w - padR, y);
            ctx.stroke();
            ctx.textAlign = "right";
            ctx.fillText(String(Math.round((g / 4) * max)), padL - 6, y + 3);
        }

        labels.forEach((label, i) => {
            const bh = (values[i] / max) * innerH;
            const x = padL + i * slot + (slot - barW) / 2;
            const y = padT + innerH - bh;
            const grad = ctx.createLinearGradient(0, y, 0, padT + innerH);
            grad.addColorStop(0, colors[i] || "#22d3ee");
            grad.addColorStop(1, "rgba(34,211,238,0.25)");
            ctx.fillStyle = grad;
            ctx.fillRect(x, y, barW, bh);
            ctx.fillStyle = "#8fa1c8";
            ctx.textAlign = "center";
            ctx.fillText(String(values[i]), x + barW / 2, y - 4);
            ctx.fillText(String(label), x + barW / 2, h - 8);
        });
    }

    function drawDonut(canvas, entries) {
        if (!canvas || !canvas.getContext) return;
        const ctx = canvas.getContext("2d");
        const dpr = window.devicePixelRatio || 1;
        const w = canvas.clientWidth || 400;
        const h = canvas.clientHeight || 240;
        canvas.width = w * dpr;
        canvas.height = h * dpr;
        ctx.scale(dpr, dpr);
        ctx.clearRect(0, 0, w, h);

        const total = entries.reduce((sum, e) => sum + e.value, 0);
        if (!total) {
            ctx.fillStyle = "#8fa1c8";
            ctx.font = "12px Segoe UI, sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("No data yet", w / 2, h / 2);
            return;
        }
        const cx = w / 2, cy = h / 2, r = Math.min(w, h) / 2 - 22;
        let angle = -Math.PI / 2;
        entries.forEach((entry) => {
            const sweep = (entry.value / total) * Math.PI * 2;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.arc(cx, cy, r, angle, angle + sweep);
            ctx.closePath();
            ctx.fillStyle = entry.color;
            ctx.fill();
            angle += sweep;
        });
        ctx.beginPath();
        ctx.arc(cx, cy, r * 0.58, 0, Math.PI * 2);
        ctx.fillStyle = "#101a3a";
        ctx.fill();
        ctx.fillStyle = "#e8eeff";
        ctx.font = "bold 20px Segoe UI, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(String(total), cx, cy + 2);
        ctx.fillStyle = "#8fa1c8";
        ctx.font = "10px Segoe UI, sans-serif";
        ctx.fillText("total", cx, cy + 16);
    }

    function legend(containerId, entries) {
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML =
            entries.map((e) => `<span><span class="swatch" style="background:${escapeHtml(e.color)}"></span>${escapeHtml(e.label)}: ${escapeHtml(e.value)}</span>`).join("");
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    async function load() {
        try {
            const [statsRes, modelRes] = await Promise.all([
                fetch("/api/stats"), fetch("/api/model-info"),
            ]);
            const stats = await statsRes.json().catch(() => ({}));
            const model = await modelRes.json().catch(() => ({}));

            // Support both old (stat-total etc) and new (analytics-stats) layouts
            setText("stat-total", stats.total_analyses ?? stats.total ?? "-");
            setText("stat-spam", stats.spam_count ?? "-");
            setText("stat-ham", stats.ham_count ?? "-");
            setText("stat-pct", stats.spam_percentage != null ? stats.spam_percentage + "%" : "-");
            setText("avg-conf", stats.average_confidence != null ? (stats.average_confidence * 100).toFixed(1) + "%" : "-");
            setText("latest-at", stats.latest_analysis_at ? new Date(stats.latest_analysis_at).toLocaleString() : "-");
            setText("ratio", stats.ham_count ? `1 : ${(stats.spam_count / Math.max(1, stats.ham_count)).toFixed(2)}` : "-");
            setText("model-name", model.available ? model.algorithm : "not trained");
            const metrics = model.metrics || {};
            setText("model-f1", metrics.f1_spam != null ? metrics.f1_spam : "-");
            setText("model-acc", metrics.accuracy != null ? metrics.accuracy : "-");

            // Fallback: if old stat elements not found but analytics-stats container exists, render summary there
            const analyticsStats = document.getElementById("analytics-stats");
            if (analyticsStats && !document.getElementById("stat-total")) {
                analyticsStats.innerHTML = `
                    <div class="stat"><strong>${escapeHtml(stats.total_analyses ?? 0)}</strong> total</div>
                    <div class="stat"><strong>${escapeHtml(stats.spam_count ?? 0)}</strong> spam</div>
                    <div class="stat"><strong>${escapeHtml(stats.ham_count ?? 0)}</strong> ham</div>
                    <div class="stat">${escapeHtml(stats.spam_percentage ?? 0)}% spam</div>
                    <div class="stat">avg conf ${(stats.average_confidence != null ? (stats.average_confidence*100).toFixed(1) : "-")}%</div>
                `;
            }

            // Risk distribution - support both old and new canvas IDs
            const riskEntries = ["HIGH", "MEDIUM", "LOW"].map((level) => ({
                label: level,
                value: (stats.risk_distribution && stats.risk_distribution[level]) || 0,
                color: COLORS[level],
            }));
            const riskCanvas = getCanvas(["chart-risk", "chart-risk-distribution"]);
            if (riskCanvas) drawDonut(riskCanvas, riskEntries.filter((e) => e.value > 0));
            legend("legend-risk", riskEntries);

            // Type distribution
            const typeEntries = Object.entries(stats.message_type_distribution || {}).map(([k, v]) => ({
                label: k.toUpperCase(), value: v, color: COLORS[k] || COLORS.blue,
            }));
            const typeCanvas = getCanvas(["chart-type", "chart-message-type", "chart-spam-vs-ham"]);
            if (typeCanvas) {
                drawDonut(typeCanvas, typeEntries.length ? typeEntries : [{label:"No data", value:1, color:"#334155"}]);
                legend("legend-type", typeEntries);
            }

            // Daily
            const days = stats.analyses_per_day || [];
            const dailyCanvas = getCanvas(["chart-daily", "chart-knowledge-usage", "chart-confidence-distribution", "chart-model-confidence"]);
            if (dailyCanvas) {
                drawBars(dailyCanvas,
                    days.length ? days.map((d) => (d.date || "").slice(5)) : ["No data"],
                    days.length ? days.map((d) => d.count || 0) : [0],
                    days.length ? days.map(() => "#22d3ee") : ["#334155"]);
            }

            // Additional new canvases: try to populate each if exists and not yet drawn
            const spamVsHamCanvas = document.getElementById("chart-spam-vs-ham");
            if (spamVsHamCanvas && spamVsHamCanvas !== typeCanvas) {
                drawDonut(spamVsHamCanvas, [
                    {label:"SPAM", value: stats.spam_count||0, color:COLORS.spam},
                    {label:"HAM", value: stats.ham_count||0, color:COLORS.ham}
                ]);
            }
            const manipCanvas = document.getElementById("chart-manipulation-techniques");
            if (manipCanvas) {
                const intentDist = stats.intent_distribution || {};
                const entries = Object.entries(intentDist).map(([k,v])=>({label:k, value:v, color:COLORS.blue}));
                if (entries.length) drawBars(manipCanvas, entries.map(e=>e.label), entries.map(e=>e.value), entries.map(e=>e.color));
                else drawBars(manipCanvas, ["No data"], [0], ["#334155"]);
            }

        } catch (error) {
            errorHandler(error, "Failed to load analytics");
            const grid = document.querySelector(".stat-grid") || document.getElementById("analytics-stats");
            if (grid) grid.innerHTML = `<div class="alert alert-error">Failed to load analytics: ${escapeHtml(error.message || error)}</div>`;
        }
    }

    // Only run on analytics page where any of the expected elements exist
    if (document.getElementById("chart-risk") || document.getElementById("chart-spam-vs-ham") || document.getElementById("stat-total") || document.getElementById("analytics-stats")) {
        load();
    } else if (document.getElementById("analytics-stats")) {
        load();
    }
})();
