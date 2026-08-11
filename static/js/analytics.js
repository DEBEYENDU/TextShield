/* TextShield - analytics page: stats + lightweight canvas charts */
(() => {
    "use strict";

    const COLORS = { HIGH: "#ef4444", MEDIUM: "#f59e0b", LOW: "#22c55e",
                     spam: "#ef4444", ham: "#22c55e", blue: "#3b82f6",
                     sms: "#22d3ee", text: "#3b82f6", email: "#8b5cf6" };

    function escapeHtml(value) {
        return String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function drawBars(canvas, labels, values, colors) {
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

        // grid
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
        document.getElementById(containerId).innerHTML =
            entries.map((e) => `<span><span class="swatch" style="background:${e.color}"></span>${e.label}: ${e.value}</span>`).join("");
    }

    async function load() {
        const [statsRes, modelRes] = await Promise.all([
            fetch("/api/stats"), fetch("/api/model-info"),
        ]);
        const stats = await statsRes.json();
        const model = await modelRes.json();

        document.getElementById("stat-total").textContent = stats.total_analyses;
        document.getElementById("stat-spam").textContent = stats.spam_count;
        document.getElementById("stat-ham").textContent = stats.ham_count;
        document.getElementById("stat-pct").textContent = stats.spam_percentage + "%";
        document.getElementById("avg-conf").textContent = (stats.average_confidence * 100).toFixed(1) + "%";
        document.getElementById("latest-at").textContent = stats.latest_analysis_at
            ? new Date(stats.latest_analysis_at).toLocaleString() : "-";
        document.getElementById("ratio").textContent = stats.ham_count
            ? `1 : ${(stats.spam_count / Math.max(1, stats.ham_count)).toFixed(2)}` : "-";
        document.getElementById("model-name").textContent = model.available ? model.algorithm : "not trained";
        const metrics = model.metrics || {};
        document.getElementById("model-f1").textContent = metrics.f1_spam != null ? metrics.f1_spam : "-";
        document.getElementById("model-acc").textContent = metrics.accuracy != null ? metrics.accuracy : "-";

        const riskEntries = ["HIGH", "MEDIUM", "LOW"].map((level) => ({
            label: level,
            value: stats.risk_distribution[level] || 0,
            color: COLORS[level],
        }));
        drawDonut(document.getElementById("chart-risk"),
            riskEntries.filter((e) => e.value > 0));
        legend("legend-risk", riskEntries);

        const typeEntries = Object.entries(stats.message_type_distribution).map(([k, v]) => ({
            label: k.toUpperCase(), value: v, color: COLORS[k] || COLORS.blue,
        }));
        drawDonut(document.getElementById("chart-type"), typeEntries);
        legend("legend-type", typeEntries);

        const days = stats.analyses_per_day || [];
        drawBars(document.getElementById("chart-daily"),
            days.map((d) => d.date.slice(5)),
            days.map((d) => d.count),
            days.map(() => "#22d3ee"));
    }

    load().catch((error) => {
        document.querySelector(".stat-grid").innerHTML =
            `<div class="alert alert-error">Failed to load analytics: ${escapeHtml(error.message)}</div>`;
    });
})();