/* TextShield - history page logic */
(() => {
    "use strict";

    const _ts = window.textshield || window.TextShield || window.App || {};
    if (!window.textshield) {
        console.warn("[TextShield] common.js not loaded before history.js - using fallback");
        window.textshield = _ts;
    }
    const escapeHtml = (_ts && _ts.escapeHtml) || function (v) {
        return String(v ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    };
    const formatTime = (_ts && (_ts.formatTime || _ts.formatDate)) || function (iso) {
        try { return new Date(iso).toLocaleString(); } catch { return String(iso ?? ""); }
    };
    const showToast = (_ts && _ts.showToast) || function () {};
    const errorHandler = (_ts && _ts.errorHandler) || console.error;

    const tbody = document.getElementById("history-body");
    const empty = document.getElementById("history-empty");
    const fType = document.getElementById("f-type");
    const fClass = document.getElementById("f-class");
    const fRisk = document.getElementById("f-risk");
    const clearBtn = document.getElementById("clear-btn");
    const prevBtn = document.getElementById("prev-btn");
    const nextBtn = document.getElementById("next-btn");
    const pageInfo = document.getElementById("page-info");

    if (!tbody) return; // not on history page

    const PAGE = 25;
    let offset = 0;
    let total = 0;

    function shortHash(hash) {
        return hash ? escapeHtml(hash.slice(0, 10)) + "&hellip;" : "-";
    }

    async function load() {
        try {
            const params = new URLSearchParams({
                limit: PAGE, offset: offset,
                direction: "desc", order_by: "timestamp",
            });
            if (fType && fType.value) params.set("input_type", fType.value);
            if (fClass && fClass.value) params.set("classification", fClass.value);
            if (fRisk && fRisk.value) params.set("risk_level", fRisk.value);

            const response = await fetch("/api/history?" + params.toString());
            const data = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(data.detail || "Failed to load history");
            total = data.total || 0;
            render(data.items || []);
        } catch (e) {
            errorHandler(e, "Failed to load history");
            if (tbody) tbody.innerHTML = `<tr><td colspan="7"><div class="alert alert-error">${escapeHtml(e.message || "Could not load history")}</div></td></tr>`;
        }
    }

    function render(items) {
        if (!tbody || !empty) return;
        empty.classList.toggle("hidden", items.length > 0);
        tbody.innerHTML = items.map((row) => `
            <tr>
                <td>${escapeHtml(formatTime(row.timestamp))}</td>
                <td>${escapeHtml((row.input_type || "").toUpperCase())}</td>
                <td><span class="badge badge-${row.classification === "SPAM" ? "spam" : "ham"}">${escapeHtml(row.classification)}</span></td>
                <td class="num">${row.confidence != null ? (row.confidence * 100).toFixed(1) + "%" : "-"}</td>
                <td><span class="badge badge-${escapeHtml(row.risk_level || "LOW")}">${escapeHtml(row.risk_level || "-")}</span></td>
                <td class="mono">${shortHash(row.message_hash)}</td>
                <td><button class="btn-ghost" data-id="${escapeHtml(row.id)}" title="Delete entry">&times;</button></td>
            </tr>`).join("");

        tbody.querySelectorAll("button[data-id]").forEach((btn) => {
            btn.addEventListener("click", async () => {
                try {
                    await fetch("/api/history/" + btn.dataset.id, { method: "DELETE" });
                    if (items.length === 1 && offset > 0) offset -= PAGE;
                    load();
                    showToast("Entry deleted", "info");
                } catch (e) {
                    errorHandler(e);
                }
            });
        });

        if (prevBtn) prevBtn.disabled = offset === 0;
        if (nextBtn) nextBtn.disabled = offset + PAGE >= total;
        if (pageInfo) pageInfo.textContent = total
            ? `showing ${offset + 1}-${Math.min(offset + PAGE, total)} of ${total}`
            : "";
    }

    if (fType) fType.addEventListener("change", () => { offset = 0; load(); });
    if (fClass) fClass.addEventListener("change", () => { offset = 0; load(); });
    if (fRisk) fRisk.addEventListener("change", () => { offset = 0; load(); });
    if (prevBtn) prevBtn.addEventListener("click", () => { offset = Math.max(0, offset - PAGE); load(); });
    if (nextBtn) nextBtn.addEventListener("click", () => { offset += PAGE; load(); });

    if (clearBtn) {
        clearBtn.addEventListener("click", async () => {
            if (!confirm("Delete ALL history entries? This cannot be undone.")) return;
            try {
                await fetch("/api/history", { method: "DELETE" });
                offset = 0;
                load();
                showToast("History cleared", "info");
            } catch (e) {
                errorHandler(e);
            }
        });
    }

    load();
})();
