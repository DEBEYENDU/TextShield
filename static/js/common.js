/* TextShield - shared frontend helpers (V2.0).
 *
 * Common utilities used by all pages: HTML escaping, the standard
 * JSON fetch wrapper with error envelope handling, and small renderers.
 * Load this BEFORE the page script in every template.
 */
(() => {
    "use strict";

    window.textshield = window.textshield || {};

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    }

    async function fetchJson(url, options = {}) {
        const response = await fetch(url, {
            headers: { "Content-Type": "application/json", ...(options.headers || {}) },
            ...options,
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            const error = data.error || {};
            throw new Error(error.message || `Request failed (${response.status})`);
        }
        return data;
    }

    function formatTime(iso) {
        try {
            return new Date(iso).toLocaleString();
        } catch {
            return iso;
        }
    }

    function badge(label) {
        const cls = String(label || "LOW").toUpperCase();
        return `<span class="badge badge-${escapeHtml(cls)}">${escapeHtml(label)}</span>`;
    }

    Object.assign(window.textshield, {
        escapeHtml, fetchJson, formatTime, badge,
    });
})();
