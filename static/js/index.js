/* TextShield - analysis page logic */
(() => {
    "use strict";

    // Defensive namespace - do not destructure directly from window.textshield
    const _ts = window.textshield || window.TextShield || window.App || {};
    if (!window.textshield) {
        console.warn("[TextShield] common.js not loaded before index.js - using fallback");
        window.textshield = _ts;
    }
    const escapeHtml = (_ts && _ts.escapeHtml) || function (v) {
        return String(v ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    };
    const apiRequest = (_ts && (_ts.apiRequest || _ts.fetchJson)) || fetch;
    const showToast = (_ts && _ts.showToast) || function () {};
    const errorHandler = (_ts && _ts.errorHandler) || console.error;

    const form = document.getElementById("analyze-form");
    const resultArea = document.getElementById("result-area");
    const errorArea = document.getElementById("error-area");
    const analyzeBtn = document.getElementById("analyze-btn");

    // If not on analyze page, exit gracefully
    if (!form || !resultArea) return;

    const tabs = document.querySelectorAll(".tab-btn");
    const panels = document.querySelectorAll(".tab-panel");

    let activeTab = "sms";

    tabs.forEach((btn) => {
        btn.addEventListener("click", () => {
            activeTab = btn.dataset.tab;
            tabs.forEach((b) => b.classList.toggle("active", b === btn));
            panels.forEach((p) => p.classList.toggle("active", p.dataset.panel === activeTab));
        });
    });

    function buildPayload() {
        if (activeTab === "email") {
            const subject = document.getElementById("email-subject").value.trim();
            const sender = document.getElementById("email-sender").value.trim();
            const body = document.getElementById("email-body").value.trim();
            const emailRaw = document.getElementById("email-raw").value.trim();
            if (emailRaw) return { input_type: "email", email_raw: emailRaw };
            return { input_type: "email", subject, sender, body };
        }
        const message = document.getElementById(activeTab + "-message").value.trim();
        return { input_type: activeTab, message };
    }

    function indicatorChips(indicators) {
        if (!indicators || !indicators.length) {
            return '<li><span class="check-cross">&#10005;</span><span>No rule-based indicators detected.</span></li>';
        }
        return indicators.map((ind) => `
            <li>
                <span class="check-mark">&#10003;</span>
                <span>
                    <b>${escapeHtml(ind.indicator)}</b>
                    <span class="chip sev-${escapeHtml(ind.severity)}">${escapeHtml(ind.severity)}</span>
                    ${ind.evidence ? `<span class="muted">&mdash; "${escapeHtml(ind.evidence)}"</span>` : ""}
                </span>
            </li>`).join("");
    }

    function urlBlock(urls) {
        if (!urls || !urls.length) return '<p class="muted">No URLs detected in this message.</p>';
        return urls.map((u) => {
            const flagged = (u.warnings || []).length > 0;
            return `
                <div class="url-row">
                    <span class="url-flag">${flagged ? "&#9888;&#65039;" : "&#10003;"}</span>
                    <div>
                        <div class="url-text">${escapeHtml(u.url)}</div>
                        <div class="url-warn">
                            host: ${escapeHtml(u.host || "?")} &middot;
                            scheme: ${escapeHtml(u.scheme || "none")}
                            ${u.is_shortened ? " &middot; shortened" : ""}
                            ${u.has_ip_host ? " &middot; raw IP host" : ""}
                            ${u.suspicious_tld ? " &middot; suspicious TLD" : ""}
                        </div>
                        ${(u.warnings || []).length
                            ? `<div class="url-warn" style="color:#fca5a5;">${u.warnings.map(escapeHtml).join(" &middot; ")}</div>`
                            : `<div class="url-warn" style="color:#86efac;">No suspicious patterns flagged (static check only).</div>`}
                    </div>
                </div>`;
        }).join("");
    }

    function ragBlock(evidence) {
        if (!evidence || !evidence.length) {
            return '<p class="muted">No knowledge-base evidence retrieved for this message (RAG unavailable or no match).</p>';
        }
        return evidence.map((e) => `
            <div class="evidence-box">
                <span class="ev-score">similarity ${escapeHtml(e.score)}</span>
                <span class="badge badge-${escapeHtml((e.category || "").replace(/_/g, "-")) || "badge-LOW"}">${escapeHtml(e.category)}</span>
                <div class="ev-src">${escapeHtml(e.source)} ${e.is_example ? "&middot; example" : ""}</div>
                <div class="ev-text">${escapeHtml(e.document && e.document.length > 420 ? e.document.slice(0, 420) + "&hellip;" : e.document)}</div>
            </div>`).join("");
    }

    function renderResult(data) {
        try {
            const cls = data.classification;
            const risk = data.risk_level;
            const source = data.explanation_source === "llm"
                ? "generated by LLM"
                : "template (LLM unavailable)";
            const intent = data.intent || {};
            const intentLabel = intent.label ? intent.label.replace(/_/g, " ") : null;
            resultArea.innerHTML = `
                <div class="result-hero">
                    <div class="hero-box flash">
                        <div class="label">Classification (ML)</div>
                        <div class="hero-value tag-${cls === "SPAM" ? "spam" : "ham"}">${escapeHtml(cls)}</div>
                        <div class="hero-sub">model: ${escapeHtml(data.model_used)}</div>
                    </div>
                    <div class="hero-box">
                        <div class="label">Confidence</div>
                        <div class="hero-value">${(data.confidence * 100).toFixed(1)}%</div>
                        <div class="hero-sub">ML probability of verdict</div>
                    </div>
                    <div class="hero-box">
                        <div class="label">Risk level</div>
                        <div class="hero-value risk-${escapeHtml(risk)}">${escapeHtml(risk)}</div>
                        <div class="hero-sub">score ${escapeHtml(data.risk_score ?? "?")}/100 &middot; ${(data.risk_factors || []).length} factor(s)</div>
                    </div>
                </div>

                <div class="grid">
                    <div class="card">
                        <h2>Why?</h2>
                        <p>${escapeHtml(data.explanation)}</p>
                        <p class="muted mt">Explanation ${escapeHtml(source)} &middot; message type: ${escapeHtml(data.message_type)}</p>
                    </div>

                    <div class="card">
                        <h2>Sender intent</h2>
                        ${intentLabel
                            ? `<p><b>${escapeHtml(intentLabel)}</b></p>
                               <p class="muted">${escapeHtml(intent.description || "")}</p>
                               ${intent.evidence ? `<p class="muted">&mdash; "${escapeHtml(intent.evidence)}"</p>` : ""}`
                            : '<p class="muted">Intent analysis unavailable.</p>'}
                    </div>

                    <div class="card">
                        <h2>Detected indicators</h2>
                        <ul class="check-list">${indicatorChips(data.indicators || [])}</ul>
                    </div>

                    <div class="card">
                        <h2>URL analysis</h2>
                        ${urlBlock(data.urls || [])}
                    </div>

                    <div class="card">
                        <h2>RAG evidence</h2>
                        ${ragBlock(data.rag_evidence || [])}
                    </div>

                    <div class="card">
                        <h2>Recommendation</h2>
                        <div class="rec-box ${data.classification === "HAM" ? "ham-safe" : ""}">${escapeHtml(data.recommended_action)}</div>
                    </div>
                </div>

                <p class="muted mt">${escapeHtml(data.disclaimer)}</p>`;
        } catch (e) {
            errorHandler(e, "Failed to render result");
        }
    }

    function showError(detail) {
        if (!errorArea) return;
        errorArea.className = "mt";
        errorArea.innerHTML = `<div class="alert alert-error">${escapeHtml(detail)}</div>`;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (errorArea) {
            errorArea.className = "mt hidden";
            errorArea.innerHTML = "";
        }
        if (resultArea) resultArea.classList.add("hidden");
        if (analyzeBtn) {
            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = '<span class="spinner"></span> Analyzing...';
        }

        const payload = buildPayload();
        console.log("[TextShield] Frontend request: analyze", payload);
        // Frontend validation
        const hasContent = payload.message && payload.message.trim() || payload.body && payload.body.trim() || payload.email_raw && payload.email_raw.trim() || payload.subject;
        if (!hasContent || (payload.message !== undefined && !payload.message.trim() && !payload.body && !payload.email_raw)) {
            // Let backend validate, but show immediate feedback if obviously empty
            if (!payload.message || !payload.message.trim()) {
                // For email, check body
                if (payload.input_type !== "email" && (!payload.message || !payload.message.trim())) {
                    showError("Please enter a message to analyze.");
                    if (analyzeBtn) {
                        analyzeBtn.disabled = false;
                        analyzeBtn.textContent = "Analyze Message";
                    }
                    console.log("[TextShield] Frontend validation failed: empty message");
                    return;
                }
            }
        }

        try {
            console.log("[TextShield] Frontend: sending API request to /api/analyze");
            const response = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const data = await response.json().catch(() => ({}));
            console.log("[TextShield] Frontend response:", response.status, data);
            if (!response.ok) {
                const detail = (data.detail || "Analysis failed.").replace(/^[\w.]+: /, "");
                console.log("[TextShield] Frontend error: API returned", detail);
                showError(detail);
                return;
            }
            console.log("[TextShield] Frontend: rendering result", data.classification);
            if (resultArea) resultArea.classList.remove("hidden");
            renderResult(data);
            if (resultArea) resultArea.scrollIntoView({ behavior: "smooth", block: "start" });
            console.log("[TextShield] Frontend: result rendered");
        } catch (error) {
            console.log("[TextShield] Frontend error: network failure", error);
            errorHandler(error, "Network error");
            showError("Network error - is the server running?");
        } finally {
            if (analyzeBtn) {
                analyzeBtn.disabled = false;
                analyzeBtn.textContent = "Analyze Message";
            }
        }
    });
})();
