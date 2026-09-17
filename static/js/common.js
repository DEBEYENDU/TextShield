/* TextShield - shared frontend helpers (V2.2)
 *
 * Common utilities used by all pages: HTML escaping, fetch wrapper,
 * date formatting, toast/spinner helpers, error handling and config.
 * Load this BEFORE any page-specific script in every template.
 * Canonical namespace: window.textshield (aliases: TextShield, App, utils)
 */
(() => {
    "use strict";

    // Ensure canonical namespace exists exactly once
    const ns = (window.textshield = window.textshield || {});
    // Alias for backward compatibility
    window.TextShield = window.TextShield || ns;
    window.App = window.App || ns;
    window.utils = window.utils || ns;

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
            throw new Error(error.message || data.detail || `Request failed (${response.status})`);
        }
        return data;
    }

    // Alias required by spec: apiRequest
    const apiRequest = fetchJson;

    function formatTime(iso) {
        try {
            return new Date(iso).toLocaleString();
        } catch {
            return String(iso ?? "");
        }
    }

    // Alias required by spec: formatDate
    const formatDate = formatTime;

    function badge(label) {
        const cls = String(label || "LOW").toUpperCase();
        return `<span class="badge badge-${escapeHtml(cls)}">${escapeHtml(label)}</span>`;
    }

    function showToast(message, type = "info", timeout = 3000) {
        let container = document.getElementById("toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "toast-container";
            container.style.position = "fixed";
            container.style.top = "1rem";
            container.style.right = "1rem";
            container.style.zIndex = "9999";
            document.body.appendChild(container);
        }
        const el = document.createElement("div");
        el.className = `alert alert-${escapeHtml(type)}`;
        el.style.marginBottom = "0.5rem";
        el.textContent = String(message ?? "");
        container.appendChild(el);
        setTimeout(() => el.remove(), timeout);
    }

    function showSpinner(target) {
        const el = typeof target === "string" ? document.querySelector(target) : target;
        if (!el) return;
        el.dataset._prevDisplay = el.style.display;
        el.style.display = "";
        if (!el.querySelector(".spinner")) {
            const sp = document.createElement("span");
            sp.className = "spinner";
            el.prepend(sp);
        }
    }

    function hideSpinner(target) {
        const el = typeof target === "string" ? document.querySelector(target) : target;
        if (!el) return;
        const sp = el.querySelector(".spinner");
        if (sp) sp.remove();
        if (el.dataset._prevDisplay !== undefined) {
            el.style.display = el.dataset._prevDisplay;
            delete el.dataset._prevDisplay;
        }
    }

    function errorHandler(error, fallbackMessage = "An error occurred") {
        const msg = (error && error.message) ? error.message : String(error || fallbackMessage);
        console.error("[TextShield]", msg, error);
        showToast(msg, "error", 4000);
        return msg;
    }

    const config = {
        apiBase: "",
        version: "2.2.0",
        agentic: false,
    };

    // Do not overwrite existing implementations on re-load (idempotent)
    if (!ns.escapeHtml) ns.escapeHtml = escapeHtml;
    if (!ns.fetchJson) ns.fetchJson = fetchJson;
    if (!ns.apiRequest) ns.apiRequest = apiRequest;
    if (!ns.formatTime) ns.formatTime = formatTime;
    if (!ns.formatDate) ns.formatDate = formatDate;
    if (!ns.badge) ns.badge = badge;
    if (!ns.showToast) ns.showToast = showToast;
    if (!ns.showSpinner) ns.showSpinner = showSpinner;
    if (!ns.hideSpinner) ns.hideSpinner = hideSpinner;
    if (!ns.errorHandler) ns.errorHandler = errorHandler;
    if (!ns.config) ns.config = config;

    // Global fallbacks for legacy page scripts that call bare showToast/escapeHtml
    if (typeof window.showToast === "undefined") window.showToast = ns.showToast;
    if (typeof window.hideSpinner === "undefined") window.hideSpinner = ns.hideSpinner;
    if (typeof window.showSpinner === "undefined") window.showSpinner = ns.showSpinner;
    if (typeof window.escapeHtml === "undefined") window.escapeHtml = ns.escapeHtml;
    if (typeof window.errorHandler === "undefined") window.errorHandler = ns.errorHandler;
    if (typeof window.apiRequest === "undefined") window.apiRequest = ns.apiRequest;
    if (typeof window.formatDate === "undefined") window.formatDate = ns.formatDate;

    // Also ensure aliases have same
    Object.assign(window.TextShield, ns);
    Object.assign(window.App, ns);
    Object.assign(window.utils, ns);
})();
