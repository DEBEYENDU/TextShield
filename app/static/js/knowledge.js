/* TextShield Knowledge JavaScript - Knowledge Explorer Page */
(() => {
    "use strict";

    const _ts = window.textshield || window.TextShield || window.App || {};
    if (!window.textshield) {
        console.warn("[TextShield] common.js not loaded before knowledge.js - using fallback");
        window.textshield = _ts;
    }
    const escapeHtml = (_ts && _ts.escapeHtml) || function(v){return String(v ?? "");};
    const showToast = (_ts && _ts.showToast) || function(m){console.log("[toast]", m);};
    const errorHandler = (_ts && _ts.errorHandler) || console.error;

    document.addEventListener("DOMContentLoaded", function () {
        try {
            initKnowledgeExplorer();
            initKnowledgeSearch();
        } catch (e) {
            errorHandler(e);
        }
    });

    function initKnowledgeExplorer() {
        fetchKnowledgeData();
    }

    function fetchKnowledgeData() {
        fetch("/api/knowledge/categories")
            .then((r) => r.json().catch(() => ({})))
            .then((data) => {
                if (data.success) displayCategories(data.data);
            })
            .catch((e) => errorHandler(e, "Failed to fetch categories"));

        fetch("/api/knowledge/tags")
            .then((r) => r.json().catch(() => ({})))
            .then((data) => {
                if (data.success) displayTags(data.data);
            })
            .catch((e) => errorHandler(e, "Failed to fetch tags"));

        fetch("/api/knowledge/articles")
            .then((r) => r.json().catch(() => ({})))
            .then((data) => {
                if (data.success) displayArticles(data.data);
            })
            .catch((e) => errorHandler(e, "Failed to fetch articles"));

        fetch("/api/knowledge/glossary")
            .then((r) => r.json().catch(() => ({})))
            .then((data) => {
                if (data.success) displayGlossary(data.data);
            })
            .catch((e) => errorHandler(e, "Failed to fetch glossary"));
    }

    function displayCategories(categories) {
        const kbGrid = document.getElementById("kb-grid");
        if (!kbGrid) return;
        if (!Array.isArray(categories)) return;
        kbGrid.innerHTML = "";
        categories.forEach((category) => {
            const div = document.createElement("div");
            div.className = "chip";
            div.title = String(category);
            div.innerText = String(category);
            div.style.cursor = "pointer";
            div.style.fontSize = "0.875rem";
            div.style.padding = "0.5rem 0.75rem";
            div.style.borderRadius = "4px";
            div.style.margin = "0.2rem";
            div.style.background = "var(--primary-light)";
            div.style.color = "var(--text-primary)";
            div.addEventListener("click", function () {
                console.log("Category clicked:", category);
            });
            kbGrid.appendChild(div);
        });
    }

    function displayTags(tags) {
        const tagCloud = document.getElementById("tag-cloud");
        if (!tagCloud) return;
        if (!Array.isArray(tags)) return;
        tagCloud.innerHTML = "";
        tags.forEach((tag) => {
            const span = document.createElement("span");
            span.className = "chip";
            span.title = String(tag);
            span.innerText = String(tag);
            span.style.fontSize = "0.75rem";
            span.style.padding = "0.25rem 0.5rem";
            span.style.margin = "0.1rem";
            span.style.background = "var(--primary-light)";
            span.style.color = "var(--text-primary)";
            span.style.cursor = "pointer";
            span.addEventListener("click", function () {
                console.log("Tag clicked:", tag);
            });
            tagCloud.appendChild(span);
        });
    }

    function displayArticles(articles) {
        const articleList = document.getElementById("article-list");
        if (!articleList) return;
        articleList.innerHTML = "";
        if (!Array.isArray(articles)) return;
        articles.forEach((article) => {
            const div = document.createElement("div");
            div.className = "mb-2";
            div.style.padding = "0.5rem";
            div.style.borderBottom = "1px solid var(--border)";
            div.innerHTML = `
                <h6 class="mb-1">${escapeHtml(article.title || "Untitled")}</h6>
                <small class="text-secondary">${escapeHtml(article.category || "Uncategorized")}</small>
                <p class="mb-0 small">${escapeHtml(article.content ? article.content.substring(0, 100) + "..." : "No content")}</p>
            `;
            articleList.appendChild(div);
        });
    }

    function displayGlossary(entries) {
        const glossaryList = document.getElementById("glossary-list");
        if (!glossaryList) return;
        glossaryList.innerHTML = "";
        if (!Array.isArray(entries)) return;
        entries.forEach((entry) => {
            const div = document.createElement("div");
            div.className = "mb-2";
            div.style.padding = "0.5rem";
            div.style.borderBottom = "1px solid var(--border)";
            div.innerHTML = `<strong>${escapeHtml(entry.term)}</strong>: ${escapeHtml(entry.definition || "No definition available")}`;
            glossaryList.appendChild(div);
        });
    }

    function initKnowledgeSearch() {
        const searchInputs = document.querySelectorAll("#kb-search, #tag-search, #article-search, #glossary-search");
        searchInputs.forEach((input) => {
            input.addEventListener("keyup", function () {
                const query = this.value.toLowerCase();
                const targetId = this.id.replace("search", "");
                const container = document.getElementById(targetId);
                if (!container) return;
                const items = container.querySelectorAll(".chip, div");
                items.forEach((item) => {
                    const text = item.innerText.toLowerCase();
                    item.style.display = text.includes(query) ? "" : "none";
                });
            });
        });
    }
})();
