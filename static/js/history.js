/* TextShield - history page logic */
(() => {
    "use strict";

    const tbody = document.getElementById("history-body");
    const empty = document.getElementById("history-empty");
    const fType = document.getElementById("f-type");
    const fClass = document.getElementById("f-class");
    const fRisk = document.getElementById("f-risk");
    const clearBtn = document.getElementById("clear-btn");
    const prevBtn = document.getElementById("prev-btn");
    const nextBtn = document.getElementById("next-btn");
    const pageInfo = document.getElementById("page-info");

    const PAGE = 25;
    let offset = 0;
    let total = 0;

    const { escapeHtml, formatTime } = window.textshield;

    function shortHash(hash) {
        return hash ? hash.slice(0, 10) + "&hellip;" : "-";
    }

    async function load() {
        const params = new URLSearchParams({
            limit: PAGE, offset: offset,
            direction: "desc", order_by: "timestamp",
        });
        if (fType.value) params.set("input_type", fType.value);
        if (fClass.value) params.set("classification", fClass.value);
        if (fRisk.value) params.set("risk_level", fRisk.value);

        const response = await fetch("/api/history?" + params.toString());
        const data = await response.json();
        total = data.total;
        render(data.items);
    }

    function render(items) {
        empty.classList.toggle("hidden", items.length > 0);
        tbody.innerHTML = items.map((row) => `
            <tr>
                <td>${escapeHtml(formatTime(row.timestamp))}</td>
                <td>${escapeHtml(row.input_type.toUpperCase())}</td>
                <td><span class="badge badge-${row.classification === "SPAM" ? "spam" : "ham"}">${row.classification}</span></td>
                <td class="num">${(row.confidence * 100).toFixed(1)}%</td>
                <td><span class="badge badge-${escapeHtml(row.risk_level)}">${row.risk_level}</span></td>
                <td class="mono">${shortHash(row.message_hash)}</td>
                <td><button class="btn-ghost" data-id="${row.id}" title="Delete entry">&times;</button></td>
            </tr>`).join("");

        tbody.querySelectorAll("button[data-id]").forEach((btn) => {
            btn.addEventListener("click", async () => {
                await fetch("/api/history/" + btn.dataset.id, { method: "DELETE" });
                if (items.length === 1 && offset > 0) offset -= PAGE;
                load();
            });
        });

        prevBtn.disabled = offset === 0;
        nextBtn.disabled = offset + PAGE >= total;
        pageInfo.textContent = total
            ? `showing ${offset + 1}-${Math.min(offset + PAGE, total)} of ${total}`
            : "";
    }

    [fType, fClass, fRisk].forEach((el) => el.addEventListener("change", () => { offset = 0; load(); }));
    prevBtn.addEventListener("click", () => { offset = Math.max(0, offset - PAGE); load(); });
    nextBtn.addEventListener("click", () => { offset += PAGE; load(); });

    clearBtn.addEventListener("click", async () => {
        if (!confirm("Delete ALL history entries? This cannot be undone.")) return;
        await fetch("/api/history", { method: "DELETE" });
        offset = 0;
        load();
    });

    load();
})();