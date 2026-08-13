# TextShield V2.0 — Product Requirements Document (PRD)

**Project Title:** TextShield — AI-Powered Semantic Message Intelligence System Using Retrieval-Augmented Generation (RAG) and Explainable AI

| Field | Value |
|---|---|
| Document Version | 2.0 |
| Status | Draft for Review |
| Owner | Product Management, in collaboration with Engineering, AI Research, and Cybersecurity teams |
| Audience | Engineering, ML/NLP research, Product, QA, Security, Documentation |
| Phase | Phase 1 — Requirements (documentation only; no implementation in scope) |

---

# 1. Executive Summary

TextShield is an AI-powered semantic message intelligence system that detects spam, phishing, and malicious social-engineering content in SMS and email messages. Unlike traditional spam filters — which rely primarily on keyword statistics and shallow machine-learning classifiers — TextShield reads a message the way a cybersecurity analyst would: it parses the message structure, extracts the entities involved, recovers the sender's intent, identifies the requested action, evaluates the social-engineering techniques in play, retrieves relevant cybersecurity knowledge from an internal knowledge base, and produces an evidence-backed classification with a transparent, human-readable explanation.

**Why this project exists.** Spam and phishing remain among the most prevalent and damaging security threats facing individuals and organizations. The annual cost of phishing-driven attacks is estimated in the hundreds of billions of dollars globally, and modern attacks have evolved beyond the crude "Nigerian prince" templates. Attackers now craft context-aware messages: legitimate-looking invoices, delivery notifications, account-verification alerts, and job offers that mirror genuine business correspondence. Keyword-based and frequency-based filters degrade precisely where this evolution matters: they cannot understand *meaning*. A message that reads like a legitimate bank notice but asks the recipient to enter credentials on a lookalike domain is granted the same statistical treatment as an innocent newsletter.

**Why traditional spam detection is insufficient.** Traditional filters operate on token statistics. Naive Bayes, TF-IDF-weighted logistic regression, and support vector machines are computationally efficient and have served well for bulk spam, but they exhibit structural weaknesses:

1. They are **content-blind**: messages with novel phrasing, deliberately obfuscated tokens ("v1agr@", "W1NNER"), or image-based payloads evade them.
2. They are **context-blind**: the same phrase ("Your account has been limited") can be benign in one context and malicious in another, and the classifier cannot tell the difference.
3. They are **intent-blind**: they never ask *what does the sender want the victim to do* — the single most predictive signal in social engineering.
4. They are **inexplicable**: the output is a probability with no supporting reasoning, which weakens user trust, hampers incident response, and prevents users from learning to recognize threats themselves.
5. They are **static**: without curation, they drift as language changes, and they cannot cite authoritative guidance in their verdicts.

**How semantic reasoning and RAG improve analysis.** TextShield addresses these weaknesses with a layered architecture:

- **Semantic NLP** understands what the message conveys beyond the words used: the roles of the entities, the emotional register (urgency, fear, reward), and the propositional content.
- **Intent analysis** recovers the sender's goal — extract credentials, transfer money, install software, harvest personal data, or drive legitimate engagement — and classifies the message by what it *asks for*.
- **Behavior analysis** examines patterns: impersonation of trusted brands, mismatched sender addresses, URL structure and domain properties, pressure to act fast, and requests that bypass normal channels.
- **Embeddings and vector search** map messages and knowledge-base documents into a shared semantic space, so that a message with *different words but the same meaning* as a documented scam still retrieves the relevant knowledge. This is the core of Retrieval-Augmented Generation (RAG).
- **RAG** grounds every analysis in retrieved, curated cybersecurity evidence. The system never "hallucinates" a citation: every retrieved knowledge item carries the actual source document, category, and chunk text.
- **An LLM layer** synthesizes retrieved evidence and indicator findings into a natural-language explanation when configured; a deterministic template engine guarantees explanations even when no LLM is available.
- **A decision engine** merges classifier output, static indicators, URL risk, and retrieved evidence into a transparent risk verdict with enumerated risk factors.
- **Explainable AI** is not an afterthought: every verdict must state what the message means, why it is suspicious or legitimate, what evidence was used, how reasoning proceeded, and what action is recommended.

TextShield's deliverable is therefore not a binary label, but an **evidence-backed reasoning report** for every message analyzed. It is designed to be fully local and open-source: the core pipeline runs on a student laptop with no paid API dependency, while remaining extensible to stronger models and larger deployments.

---

# 2. Vision Statement

To become the trusted, transparent eyes through which ordinary people see the true intent hidden inside every digital message — a system that does not merely say "spam" or "not spam," but shows *why*, with evidence a school student and a security professional can both act on.

---

# 3. Mission Statement

To build and continuously improve an open, local-first, explainable semantic message intelligence platform that protects individuals and organizations from phishing, spam, and social engineering by combining semantic NLP, behavioral analysis, and retrieval-augmented reasoning — delivering evidence-backed verdicts and recommendations that educate users as it protects them.

---

# 4. Background

## 4.1 Current spam detection methods

Spam detection is one of the oldest applied machine-learning problems in industry. Deployed systems combine several layers:

- **Header/transport filtering:** rejection based on sender reputation, IP blacklists, SPF/DKIM/DMARC authentication failures, and greylisting.
- **Content filters:** statistical classifiers (Naive Bayes, logistic regression, gradient-boosted trees) over tokenized message text, often feature-weighted with TF-IDF.
- **Heuristic rule engines:** hand-crafted rules ("contains >3 exclamation marks", "money-gram mentions", "urgency lexicon matches") scored into a final verdict, as in classic SpamAssassin-style systems.
- **Collaborative feedback:** user "report spam" actions aggregate into corpus-level signals (e.g., shared spam signatures).
- **Deep-learning models:** character/word-level neural networks (CNNs, LSTMs, BERT-style transformers) that learn local and contextual patterns directly from text.

## 4.2 Current phishing detection methods

Phishing detection spans message-level and infrastructure-level defenses:

- **URL reputation and domain analysis:** checks against blocklists (Google Safe Browsing, PhishTank) and domain-similarity heuristics ("paypa1.com", "account-verify-bank.xyz").
- **Brand impersonation detection:** models trained to recognize known-brand mentions co-occurring with credential-request patterns.
- **Sender authentication:** SPF/DKIM/DMARC alignment checks for email.
- **Visual/screenshot analysis:** computer-vision systems that compare a rendered page to brand templates.
- **User awareness training and simulated phishing:** the human layer, teaching people to recognize cues.
- **Post-hoc reporting and takedown:** abuse-desk processing of reported URLs (this is reactive, not preventive).

## 4.3 Current limitations

| Limitation | Explanation |
|---|---|
| Statistical blindness | Novel, obfuscated, or image-heavy content escapes frequency-based models. |
| Context blindness | Identical or near-identical text is judged identically even when context differs. |
| Intent blindness | Filters never model what the sender wants the victim to do. |
| Adversarial fragility | Attackers run their own classifiers against filters and mutate wording until evasive. |
| Explainability gap | A probability score provides no reasoning, evidence, or lesson for the user. |
| Knowledge separation | Filters cannot cite, retrieve, or reason over curated cybersecurity guidance. |
| Static drift | Models without continuous curation decay as language and tactics evolve. |
| False-positive harm | Aggressive statistical filtering silently drops legitimate mail (delivery notices, one-time passwords) — a real cost. |

## 4.4 Need for semantic understanding

A filter that understands meaning can evaluate *paraphrases of the same scam* uniformly, distinguish a benign brand mention from an impersonation request, and reason about the structure of the message (who wrote it, to whom, about what, asking for what). Semantic understanding is the prerequisite for treating messages as miniature social interactions rather than bags of words.

## 4.5 Need for explainability

Explainability drives three outcomes: (a) **user trust** — people act on warnings they understand; (b) **user education** — each explanation trains the user to recognize future threats; (c) **accountability and audit** — security teams, researchers, and regulators can inspect *why* a verdict was issued, which is mandatory in regulated environments handling consumer communications.

## 4.6 Need for RAG

Static models know only what their training data showed. RAG connects the model to a **curated, updateable knowledge base** at inference time: the message is embedded, semantically similar knowledge documents are retrieved, and the nearest matches become cited evidence. This provides (a) grounding — claims traced to real sources; (b) freshness — knowledge updated without retraining; (c) coverage — long-tail attack descriptions that never appeared in training samples; and (d) reduced hallucination — the LLM composes over retrieved text rather than from memory alone.

---

# 5. Problem Statement

Modern automated messaging threats increasingly exploit *human cognition*, not technical vulnerabilities. A phishing email that mimics a courier's style, a scam SMS that impersonates a bank's shortcode, and a fake job offer targeting students all share a common property that statistical filters cannot see: they are **engineered conversations** whose dangerous content lies in their *intent and structure*, not their vocabulary.

The concrete problems this project addresses:

1. **Detection failure on novel attacks.** Because statistical filters are fitted to historical token distributions, previously unseen phrasings — the norm in targeted attacks — produce uncertain or incorrect verdicts exactly when risk is highest.
2. **No reasoning that users can act on.** Even when a verdict is correct, users receive no explanation; expected personalization of error messages and warnings is absent, reducing both trust and the user's ability to generalize to future threats.
3. **No retrieval of authoritative guidance.** Existing filters cannot connect a message to documented scam categories, behavioral patterns, or safety guidance at analysis time, so the analysis cannot be grounded in curated knowledge.
4. **One-dimensional assessment.** Current systems separate "spam classification" from "phishing detection" from "URL analysis"; no single tool combines semantic meaning, sender intent, behavior patterns, and evidence into one coherent risk decision.
5. **Closed, opaque decision pipelines.** Users and researchers cannot audit the reasoning chain (feature → indicator → evidence → verdict), which blocks education, research, and trust.

The problem statement, in one sentence: *Individuals and organizations receive socially engineered messages whose danger lies in meaning and intent rather than vocabulary alone, and existing statistical filters neither detect such messages reliably nor explain their decisions; therefore, a semantic, retrieval-augmented, explainable message intelligence system is required.*

---

# 6. Existing Systems

This section surveys current spam-filtering approaches, their strengths, and their weaknesses. It frames the design space TextShield enters.

## 6.1 Keyword filtering

**How it works.** Messages containing flagged tokens ("win", "free", "casino", "viagra") are scored or blocked by rule.

| Advantages | Disadvantages |
|---|---|
| Extremely fast; trivially explainable | Easily bypassed by obfuscation and synonyms |
| Simple to deploy and tune | High false-positive rate on innocent use of the same words |
| No training data required | No understanding of context or intent |
| | Rule lists require constant manual maintenance |

## 6.2 Naive Bayes

**How it works.** Assumes token independence and applies Bayes' theorem to compute the probability a message is spam given its token frequencies, typically smoothed (Laplace/alpha) over a labeled corpus.

| Advantages | Disadvantages |
|---|---|
| Simple, fast, works with small data | Independence assumption is false for natural language |
| Robust baseline; solid on bulk spam | Weak on targeted, novel, or obfuscated messages |
| Easy to implement and inspect | Predicts from word *presence*, not message *meaning* |
| Online variants adapt to feedback | Gives no explanation of intent; mistakes are opaque |

## 6.3 TF-IDF + linear models (Logistic Regression, SVM)

**How it works.** Text is converted to TF-IDF-weighted vector features (optionally with n-grams); a regularized linear classifier (logistic regression or linear SVM/hinge loss) learns separating hyperplanes over the feature space.

| Advantages | Disadvantages |
|---|---|
| State-of-the-art among classical text methods | Features are still lexical, not semantic |
| Strong accuracy with modest compute | Requires feature engineering and tuning |
| Calibrated probabilities possible (LR) / margin scores (SVM) | Degrades on vocabulary drift and obfuscation |
| Interpretable feature weights | Same "meaning" with different words gets different vectors |
| Low memory footprint at inference | Cannot incorporate outside knowledge at runtime |

## 6.4 Neural approaches (CNNs, RNNs, transformers)

**How it works.** Deep models ingest token (or subword) sequences. CNNs extract local n-gram-like patterns; RNNs/LSTMs model word order; transformer models (BERT-family) pretrain on enormous corpora and fine-tune on spam classification. Embedding layers make *similar meanings* map to *similar vector positions*.

| Advantages | Disadvantages |
|---|---|
| Best-in-class accuracy; handles word order | High training cost; large memory and GPU needs |
| Semantic generalization via embeddings | "Black box": decisions are difficult to explain |
| Transformers capture context and nuance | Risk of hallucinated or ungrounded explanations |
| Good with obfuscation and paraphrasing | Slow inference relative to linear models |
| | Deployment overhead (model size, serving infra) |

## 6.5 Industry composites (e.g., SpamAssassin-style stacks)

**How it works.** Production systems fuse many signals: header checks, DNS/blacklist lookups, content rules with scores, statistical classifiers, and user/network feedback.

| Advantages | Disadvantages |
|---|---|
| High detection rates in practice | Architecture complexity and tuning burden |
| Redundancy across signal types | Verdict still lacks *reasoning*, only composite score |
| Standardized in mail infrastructures | No explanation for recipients; hard to audit |
| | Knowledge base (rules) is static, human-maintained |

## 6.6 Gap analysis

Across every family above, three systemic gaps persist: **(G1) no semantic understanding of intent and meaning;** **(G2) no runtime retrieval of curated cyber-knowledge to ground decisions;** **(G3) no explainable, evidenced reasoning delivered to the user.** TextShield is designed specifically to close G1–G3 while retaining the strengths of classical ML (speed, calibration, low resource use) as its decision backbone.

---

# 7. Proposed Solution

## 7.1 What TextShield is

TextShield is a semantic message intelligence system whose analysis pipeline treats each message as a communicative act: *who is addressing whom, about what, in what tone, requesting what, with what evidential basis — and is that request legitimate?* The system produces a risk verdict (SPAM/HAM with calibrated confidence), a severity level (LOW / MEDIUM / HIGH / CRITICAL / UNCERTAIN), a list of evidence, and a natural-language explanation, all in a single structured response.

## 7.2 Why TextShield is different

| Dimension | Traditional filters | TextShield |
|---|---|---|
| Unit of analysis | Token frequencies | Meaning, intent, behavior, structure |
| Verdict | Probability/label | Label + confidence + risk level + factors |
| Evidence | None | Indicators, URL findings, retrieved knowledge, model output |
| Explanation | None | Template or LLM-generated, always present |
| Knowledge | Fixed at training | Curated KB retrieved at runtime (RAG) |
| Auditability | Opaque | Full reasoning chain exposed via API and UI |
| Operating model | Black-box scoring | Analyst-style reasoning with fallbacks |

## 7.3 Component roles

- **Semantic NLP.** Normalizes messages (with privacy-preserving redaction of phones/emails/money/URLs into placeholders), tokenizes, and feeds meaning-preserving features to the classifier while separate analyzers extract structure.
- **Intent Analysis.** Determines the sender's goal class — e.g., *credential harvesting*, *money movement*, *software installation*, *identity data collection*, *engagement* — derived from imperative phrasing ("click", "verify", "transfer", "download"), requested actions, and urgency cues.
- **Behavior Analysis.** Scores social-engineering behaviors: brand impersonation, sender/URL mismatch, address deceptiveness, pressure-to-act, reward bait (prizes/refunds), authority claims, and channel bypass ("we couldn't reach you by phone").
- **Entity Extraction.** Extracts and redacts emails, phone numbers, URLs, monetary amounts, and named entities, retaining presence/type signals for analysis while protecting user data.
- **Embeddings.** A sentence-transformer model maps both messages and knowledge-base documents to dense vectors in a shared semantic space (with a lightweight fallback model if the primary is unavailable).
- **Vector Search.** A local vector database (chromadb backend) performs similarity retrieval over embedded knowledge chunks; the store is built from a curated knowledge base and rebuilt on demand.
- **RAG.** At inference, the message embedding retrieves the top-k semantically closest knowledge chunks; these become *cited evidence* and are passed to the explanation generator.
- **LLM.** When configured (local Ollama or compatible provider), synthesizes retrieved evidence plus indicator findings into fluent explanations; absent configuration, a deterministic template engine produces the explanation — the system never depends on LLM availability.
- **Evidence Validation.** Every piece of retrieved evidence is a real document chunk from the knowledge base; the retriever returns source document names, categories, and chunk text. No fabricated citations.
- **Decision Engine.** A transparent risk engine merges: calibrated classifier output, indicator severities, URL analysis findings, and RAG evidence into a risk level plus enumerated risk factors, using documented, auditable logic.
- **Explainable AI.** The response surface guarantees: meaning summary, suspicion reasons, legitimacy reasons, evidence list, reasoning trace, and recommended action — for every analysis.

## 7.4 Architectural pillars

1. **ML-first decisioning.** The trained classifier casts the verdict; RAG/LLM enrich and explain but do not override the classification. This keeps decisions deterministic and testable.
2. **Graceful degradation.** Missing model → explicit 503; missing vector store → analysis without evidence; missing LLM → template explanation. Each layer is individually optional except (a) the classifier and (b) the explanation surface.
3. **Transparency by default.** Every endpoint and page exposes indicators, URL findings, retrieved knowledge, risk factors, and model/version metadata.
4. **Local-first, open-source.** Runs on commodity hardware; no paid API is required for the core product; privacy is preserved by on-device, hashed-history storage.

---

# 8. Project Objectives

## 8.1 Primary objectives

| ID | Objective | Success indicator |
|---|---|---|
| PO-1 | Build a semantic message intelligence system that classifies SMS and email as SPAM or HAM with calibrated confidence | Verified classification accuracy ≥ 95% on the evaluation hold-out set with calibration quality (Brier/ECE) reported |
| PO-2 | Detect and explain social-engineering intent (credential harvesting, money movement, urgency) | Intent/behavior indicators exposed for ≥ 90% of synthetic phishing test messages |
| PO-3 | Ground verdicts in retrieved, cited knowledge-base evidence via RAG | ≥ 1 relevant evidence item retrieved and cited for ≥ 85% of test scam messages |
| PO-4 | Provide explainable verdicts (meaning, suspicion, legitimacy, evidence, reasoning, recommendation) for every analysis | 100% of API responses include the full explanation surface |
| PO-5 | Deliver a usable web dashboard (analyze, history, analytics, knowledge base, about) | All dashboard pages verified functional; core user journey completes end-to-end |

## 8.2 Secondary objectives

| ID | Objective |
|---|---|
| SO-1 | Maintain privacy by design: content redaction and hashed history storage by default |
| SO-2 | Keep the pipeline runnable on a student laptop without paid APIs |
| SO-3 | Expose structured analytics (volume, verdict mix, risk distribution, indicator frequency) |
| SO-4 | Provide knowledge-base management and rebuild tooling |
| SO-5 | Document architecture, ML pipeline, RAG pipeline, API, and setup for external readers |

## 8.3 Research objectives

| ID | Objective |
|---|---|
| RO-1 | Quantify the contribution of each layer (classifier, indicators, URL analysis, RAG evidence) to overall verdict quality |
| RO-2 | Compare classical (TF-IDF + linear) versus embedding-based decision backbones on the same corpus |
| RO-3 | Measure the value of retrieved evidence for explanation quality (groundedness, usefulness) |
| RO-4 | Evaluate fallback behaviors (template vs LLM explanations) for consistency and safety |

## 8.4 Learning objectives

| ID | Objective |
|---|---|
| LO-1 | Practice the full ML lifecycle: dataset preparation, training, evaluation, packaging, deployment |
| LO-2 | Apply NLP concepts end-to-end: preprocessing, feature engineering, embeddings, semantic search |
| LO-3 | Apply cybersecurity knowledge: phishing taxonomies, social-engineering patterns, safe URL analysis |
| LO-4 | Practice RAG systems engineering: knowledge curation, chunking, embedding, retrieval, generation |
| LO-5 | Practice professional product discipline: requirements engineering, documentation, testing, release |

---

# 9. Scope

## 9.1 In scope

1. Analysis of **SMS text messages** (typed or pasted).
2. Analysis of **email messages** — both structured fields (subject/sender/body) and **raw email with headers** (auto-detected and parsed).
3. SPAM/HAM classification with calibrated confidence.
4. Risk assessment with severity levels (LOW / MEDIUM / HIGH / CRITICAL / UNCERTAIN) and enumerated risk factors.
5. Indicator engine covering: urgency/pressure language, financial language, credential-request language, brand impersonation, link-shortener/URL risk, deceptive sender cues, and reward-bait language.
6. Static URL analysis: scheme, domain entropy, suspicious TLD patterns, IP-literal URLs, redirect/shortener detection, and domain-similarity heuristics.
7. Semantic embeddings via a local sentence-transformer (with a built-in fallback model) for both messages and knowledge documents.
8. Local vector store (chromadb backend) with knowledge ingestion, chunking, querying, and rebuild.
9. RAG retrieval that returns only real, cited knowledge chunks (source document, category, chunk text).
10. LLM-based explanation generation when a local LLM is configured, with a deterministic template engine fallback — the explanation surface is always present.
11. History storage (message content stored hashed by default) with retrieval, deletion (single/clear-all), and statistics.
12. Analytics: volume, classification mix, risk distribution, top indicators, model information.
13. Knowledge-base browsing and management (categories, documents, rebuild trigger).
14. Web dashboard (analyze, history, analytics, knowledge base, about) and a documented REST API for programmatic use.
15. Model lifecycle tooling: dataset preparation, training with automatic algorithm selection, evaluation reports, and artifact packaging.
16. Documentation: setup, architecture, ML pipeline, RAG pipeline, API reference, and this PRD.
17. Automated test suite covering preprocessing, classifier, indicators, URL analyzer, risk engine, RAG, and API behavior.

## 9.2 Out of scope (V2.0)

1. Real-time email/sms protocol integration (IMAP/SMTP/MMS ingestion, mail server plugins).
2. Attachment scanning, file-content analysis, and malware sandboxing.
3. URL fetching/crawling of analyzed links (reputation checks are static only).
4. Image/visual analysis of message content or screenshots.
5. Multi-language message analysis beyond English (architecture permits later extension).
6. Cloud, multi-tenant, or distributed deployment; horizontal scaling; high-availability clusters.
7. Continuous retraining pipelines, A/B model serving, or MLOps platforms.
8. Mobile applications or browser extensions.
9. Commercial threat-intelligence feeds and paid reputation services.
10. Blocking/enforcement actions on mail servers (the system advises; it does not act).

---

# 10. Stakeholders

| Stakeholder | Role in the project | Interests and expectations |
|---|---|---|
| End users (students, general public) | Primary analyzers of received messages | Simple, trustworthy verdicts; clear explanations; no technical burden; privacy |
| Cybersecurity learners/researchers | Use the system as a teaching and research instrument | Auditable reasoning, evidence links, documented methods, reproducible pipeline |
| Organizations and businesses | Pilot deployments for employee protection | Accurate detection, explanation that supports training, auditable history, simple operations |
| University/college administration | Hosts/credits the project context | Professional documentation, demonstrable academic depth, ethical use |
| Product management | Defines requirements, priorities, acceptance | Requirement traceability, measurable KPIs, on-schedule phases |
| Engineering team | Designs, builds, tests, operates the system | Clear requirements, maintainable architecture, testable acceptance criteria |
| ML/NLP research team | Models, embeddings, retrieval quality | Defined research objectives, evaluation protocol, reproducibility |
| Cybersecurity analysts | Validate knowledge-base content and risk logic | Accurate taxonomies, current scam intelligence, evidence correctness |
| QA/Testing | Verify requirements are met | Measurable acceptance criteria, testable surfaces (API + UI) |
| Documentation/technical writing | Produce and maintain docs | Complete, structured input (this PRD), clear terminology |
| Privacy/legal advisors | Oversee data handling | Privacy-by-design compliance, transparent data flows, consent options |
| GitHub community / open-source users | Consume and extend the product | Clear README, licensing, contribution guidance, issue tracking |

---

# 11. Target Users

| Persona | Description | Primary needs | Example intent |
|---|---|---|---|
| Students | Frequent targets of fake job offers, scholarship scams, exam-related phishing; limited security training | Quick, credible verdicts; educational explanations; privacy | "Is this 'work from home' offer a scam?" |
| General users | Everyday SMS/email recipients; legacy users of Gmail/outlook-style filters | Simple verdict, plain-language explanation, minimal friction | "Is this bank message real?" |
| Researchers | Academics studying spam, phishing, NLP, or XAI | Reproducible pipeline, documented methods, exposed reasoning | "Can I inspect which evidence drove this verdict?" |
| Organizations | SMEs and departments defending staff from email/SMS fraud | Accurate triage, reportable analytics, history audit | "How many high-risk messages reached staff this month?" |
| Businesses | Firms under brand-impersonation attacks | Phishing taxonomy coverage, explainable alerts for their brand | "Why was this invoice flagged?" |
| Cybersecurity learners | People training to become analysts | Case studies: real messages + evidence + reasoning chain | "What techniques does this message use?" |
| Students of ML/NLP | Learners of applied NLP engineering | Full pipeline transparency, fallback design, clean interfaces | "Where does the ML output come from?" |

---

# 12. Functional Requirements

Numbering: FR-XX. Priority: MUST / SHOULD / MAY. Every requirement below is testable via the acceptance criteria in Section 28.

## 12.1 Message analysis (core)

### FR-01 Message intake
- **MUST.** The system accepts analysis requests for: (a) plain SMS-style text; (b) structured email fields (subject, sender, body, optional raw email); (c) raw email pasted as one block.
- **MUST.** A message submitted to the generic text input is auto-detected as raw email when its first lines match header markers (`From:`, `Subject:`, `To:`, `Date:`), and then analyzed as an email (subject/sender/body extracted).
- **MUST.** Empty or whitespace-only messages are rejected with a clear validation error.
- **MUST.** Both the REST API (`POST /api/analyze`) and the web form produce identical analysis results.

### FR-02 Analysis pipeline execution
- **MUST.** Every analysis executes, in order: input parsing → normalization/redaction → extraction (URLs, emails, phones, money) → classifier prediction → indicator evaluation → URL analysis → RAG retrieval → risk computation → explanation generation → (optional) history persistence.
- **MUST.** The pipeline never skips the explanation surface, even when RAG or LLM layers fail.

### FR-03 SPAM/HAM classification
- **MUST.** Return a primary classification label (`SPAM` or `HAM`) and a calibrated probability/confidence value.
- **MUST.** Identify which model produced the verdict (model name/version) in the response.
- **SHOULD.** Provide the probability implicitly used for calibration, exposed in the API payload.

### FR-04 Risk assessment
- **MUST.** Return a risk level from the ordered set LOW < MEDIUM < HIGH < CRITICAL, plus the special value UNCERTAIN.
- **MUST.** Return a list of individual risk factors with reasoning, so the level is derivable from its parts.
- **MUST.** If the classifier is unavailable, surface a clear service-level error (503-class) rather than a fabricated risk.

## 12.2 Semantic understanding and intent

### FR-05 Semantic preprocessing
- **MUST.** Normalize text deterministically: lowercasing, whitespace canonicalization, and replacement of phones/emails/URLs/money amounts with stable placeholders (`[PHONE]`, `[EMAIL]`, `[URL]`, `[MONEY]`).
- **MUST.** Keep redacted placeholders in the feature space so the classifier learns *presence* signals.
- **SHOULD.** Support tokenization with an optional stop-word removal mode (off by default) for experimentation.

### FR-06 Intent extraction
- **MUST.** Derive the sender's requested action category from message language, including at least: credential request, money transfer, download/install, personal-data request, prize/reward claim, information confirmation, and benign engagement.
- **MUST.** Surface intent-related indicators separately from lexical classification (e.g., "requests credentials via link").
- **SHOULD.** Return a machine-readable intent label alongside human text.

### FR-07 Behavior analysis
- **MUST.** Evaluate behavioral cues: brand impersonation, urgency/pressure, financial bait, authority claims, channel bypass, link reliance, and deceptive sender-signal mismatches.
- **MUST.** Attach severity (low/medium/high) and category to every matched indicator, with supporting evidence text excerpted from the message.

## 12.3 Entity extraction and URL analysis

### FR-08 Entity extraction
- **MUST.** Detect URLs, email addresses, phone numbers, and monetary amounts within messages.
- **MUST.** Redact detected entities before history storage unless the user explicitly opts into storing readable content.

### FR-09 URL analysis
- **MUST.** Analyze each URL statically: scheme (http/https), host entropy/readability, suspicious TLDs, IP-literal hosts, link-shortener domains, and look-alike domains against known brands.
- **MUST.** Return per-URL findings with severity and a plain-language description.
- **SHOULD.** Flag URLs whose visible text/domain mismatch the sender's claimed brand.

## 12.4 RAG retrieval and knowledge grounding

### FR-10 Knowledge-base ingestion
- **MUST.** Ingest markdown knowledge documents organized by category: scam types (banking, email, SMS, job, loan, investment, phishing), behavioral patterns (urgency, reward, URL tactics, social engineering), legitimate-communication guidance, safety guidelines, examples, and reference material.
- **MUST.** Chunk documents deterministically, embed chunks with the active embedding provider, and persist the index (structure metadata: chunk counts, document counts, categories, build timestamp).
- **MUST.** Support rebuild of the vector index from the knowledge base on demand.

### FR-11 Retrieval
- **MUST.** At analysis time, embed the message and retrieve the top-k most similar knowledge chunks.
- **MUST.** Return only real chunks with source document names, categories, and text; the retriever must never fabricate evidence.
- **MUST.** Operate with graceful fallback: if the index is missing, analysis continues without evidence and the response states `rag_status.ready = false`.

### FR-12 Retrieval health/status
- **MUST.** Expose vector-store status (backend, embedding provider, chunk/document counts, categories, build time) in API responses and the dashboard.
- **SHOULD.** Cache status reads for a short TTL to avoid needless disk access on every analysis.

## 12.5 Explainability and recommendations

### FR-13 Explanation surface
- **MUST.** Every analysis response contains the six explanation components: (1) what the message means/claims, (2) why it is suspicious, (3) why it may be legitimate, (4) evidence used, (5) reasoning summary, (6) recommended action.
- **MUST.** Generate explanations from a deterministic template engine when no LLM is configured or available, and from the LLM when configured.
- **MUST.** State the explanation source (`template`/`llm`) in the response for auditability.

### FR-14 Recommendation engine
- **MUST.** Provide a recommended action appropriate to the risk level (e.g., CRITICAL: do not click links, do not reply, report to provider/CERT; LOW: confirm with known sender channel).
- **MUST.** Recommendations reference the same evidence used by the verdict (no new, ungrounded claims).

## 12.6 History and privacy controls

### FR-15 History store
- **MUST.** Persist analysis records (timestamp, verdict, confidence, risk level, message type, optionally content, model used, RAG status) to local SQLite.
- **MUST.** List history with pagination, fetch statistics, delete a single record, and clear all records via API and UI.
- **MUST.** Store message content **hashed (SHA-256) by default**; readable content is stored only when the user opts in per analysis.

### FR-16 History UI
- **MUST.** Render history with verdict badges, risk level, timestamps, and content (redacted/hashed when applicable), plus filter and pagination controls.
- **SHOULD.** Show computed statistics summary (totals by verdict and risk) in the history view.

## 12.7 Analytics

### FR-17 Analytics
- **MUST.** Expose aggregate statistics: total analyses, verdict distribution, risk-level distribution, average confidence, top indicators, top risk factors, and model information.
- **MUST.** Render analytics on a dedicated dashboard page with charts drawn locally (no external CDNs).
- **SHOULD.** Expose the same aggregates via `/api/stats` for external consumption.

## 12.8 Dashboard and pages

### FR-18 Pages and navigation
- **MUST.** Provide the following pages, reachable from a shared navigation: Analyze (home), History, Analytics, Knowledge Base, About.
- **MUST.** The Analyze page supports the message-type tabs (SMS text, email fields, raw email) with live/on-submit analysis and a readable result panel showing verdict, risk, indicators, evidence, explanation, and recommendation.
- **MUST.** The Knowledge Base page lists categories and documents with counts and offers a rebuild action.
- **MUST.** The About page presents project background, architecture summary, model details, and privacy statement.
- **SHOULD.** Provide responsive layouts usable on desktop and mobile browsers.

### FR-19 REST API
- **MUST.** Expose at least: `POST /api/analyze`, `GET /api/history`, `DELETE /api/history/{id}`, `DELETE /api/history`, `GET /api/stats`, `GET /api/model-info`, `GET /api/health`, `GET /api/knowledge-base`, `POST /api/knowledge-base/rebuild`.
- **MUST.** Return structured JSON with stable schemas; document every endpoint in the API reference.
- **MUST.** Provide error responses with machine-readable detail (validation 422, unavailable 503, internal 500) and never leak stack traces.

## 12.9 Model and knowledge management

### FR-20 Model lifecycle tooling
- **MUST.** Provide scripts for: dataset preparation, model training (with automatic algorithm selection and calibration), evaluation (metrics report + confusion matrix + per-class report), and artifact packaging.
- **MUST.** Model artifacts include the classifier, vectorizer, metadata (algorithm, features, training date, corpus size), and evaluation report.
- **SHOULD.** The web UI surfaces model metadata (name, features, trained date, evaluation summary).

### FR-21 Knowledge-base management
- **MUST.** Allow browsing knowledge-base categories and documents in the UI and API.
- **MUST.** Rebuild the vector index from current knowledge documents on demand (UI button and `POST /api/knowledge-base/rebuild`).
- **MUST.** Reflect rebuild completion and status (document/chunk counts) in the UI.

## 12.10 Configuration

### FR-22 Configuration
- **MUST.** Runtime configuration via environment variables with sensible defaults: embedding provider (sentence-transformers / fallback), vector-db path and backend, RAG top-k, LLM provider and model (empty model ⇒ LLM disabled ⇒ template mode), history/content-storage defaults, data/model paths, port and host.
- **MUST.** Document all configuration keys with defaults and effects (`.env.example` + setup guide).
- **SHOULD.** Validate configuration at startup and log clear warnings for unused or invalid values.

---

# 13. Non-Functional Requirements

### NFR-01 Performance
- **MUST.** Analysis of a typical SMS message completes in under 5 seconds on the reference hardware (student laptop, CPU-only) including embedding and retrieval.
- **MUST.** Dashboard static pages respond in under 500 ms server-side.
- **MUST.** Vector retrieval stays under 500 ms for the shipped knowledge base size.
- **SHOULD.** Serve concurrent analyses without serializing on the DB; use thread-safe connection handling.

### NFR-02 Scalability
- **SHOULD.** Support growth from the shipped knowledge base (≈100 chunks) to 10× size with no architectural change (chunked ingestion, query limits).
- **MAY.** Support horizontal scale-out (multiple workers) without shared-state corruption in the local-first deployment model.

### NFR-03 Reliability
- **MUST.** Graceful degradation chain: every optional layer (RAG, LLM) failing must not take down analysis; the system returns a complete response with clear status flags.
- **MUST.** A history-write failure never breaks an analysis response (persistence is wrapped and isolated).
- **MUST.** The application recovers on restart: missing indexes are rebuilt or reported, never silently broken.

### NFR-04 Security
- **MUST.** No secrets in code or repositories; all keys via environment variables (`.env` ignored by VCS).
- **MUST.** No default credentials; no admin backdoor; no remote code-execution surface in public APIs.
- **MUST.** Sanitize all user-supplied content rendered in pages (strict output encoding) to prevent stored XSS.
- **MUST.** Enforce content-length limits on analysis payloads; reject oversized bodies.
- **MUST.** Rate-limit or otherwise bound history deletion/rebuild actions appropriate to a local-first product.
- **SHOULD.** Bind the server to localhost by default; document exposure guidance for LAN use.

### NFR-05 Availability
- **MUST.** Core analysis (classifier + template explanations) works with zero external network calls.
- **MUST.** The system starts and reports health through `/api/health` even when model/RAG components are absent (degraded status).

### NFR-06 Privacy
- **MUST.** Content privacy by default: phone numbers, emails, URLs, and money amounts are redacted before storage; raw content is stored hashed unless the user opts in.
- **MUST.** No user message content is transmitted to third parties; embedding and retrieval are fully local by default.
- **MUST.** Document the privacy model (what is stored, how, for how long, and how it is deleted) on the About page and in the setup guide.

### NFR-07 Maintainability
- **MUST.** Modular architecture with clear boundaries: core config, ML, RAG, services, API, database, templates, static assets — documented in the architecture guide.
- **MUST.** Automated test suite covering all modules; CI-runnable with a single command.
- **MUST.** Logging with levels and consistent formats; errors carry component context.
- **SHOULD.** Code follows a consistent documented style (PEP 8-compatible, type-hinted public interfaces).

### NFR-08 Portability
- **MUST.** Run on Windows and Linux Python 3.10+ with the documented dependency set (CPU-only).
- **MUST.** Dependencies pinned/constrained for reproducibility; setup guide covers virtual environments.

### NFR-09 Accessibility
- **SHOULD.** Pages are keyboard-navigable; verdicts and risk levels are not communicated by color alone (labels/badges include text).
- **SHOULD.** Sufficient contrast ratios for all UI text and status colors.

### NFR-10 Usability
- **MUST.** The analyze flow from paste-to-verdict requires no more than one click after input.
- **MUST.** Explanations are written in plain language understandable by a non-technical user; jargon is accompanied by definitions (glossary linked from the UI footer).
- **SHOULD.** Provide inline validation messages for malformed inputs rather than server-side-only errors.

---

# 14. User Stories

| ID | As a(n)… | I want to… | So that… |
|---|---|---|---|
| US-01 | general user | paste a suspicious SMS and receive a verdict with plain-language explanation | I can decide what to do without consulting an expert |
| US-02 | general user | paste a raw email with headers into the text box and have it analyzed as an email | I don't need to know header syntax |
| US-03 | student | analyze a "work from home" job offer | I can tell whether it is a job scam before sharing any details |
| US-04 | researcher | see which knowledge-base documents were retrieved for a verdict | I can audit the grounding of every decision |
| US-05 | analyst | see every matched indicator with severity and evidence excerpt | I can triage alerts rapidly and defend the verdicts to others |
| US-06 | user | know whether my message content is stored and how | I can trust the system with sensitive communications |
| US-07 | user | delete individual history records or clear all history | I remain in control of my data |
| US-08 | admin | rebuild the knowledge-base index from the UI | I can update knowledge without touching the server |
| US-09 | manager | view analytics (volume, verdict mix, risk distribution) | I can report threat pressure within my organization |
| US-10 | ML engineer | retrain the model with a single script and see an evaluation report | I can improve accuracy reproducibly |
| US-11 | learner | read a step-by-step reasoning summary for a flagged message | I learn to recognize the technique next time |
| US-12 | organization | receive a recommendation with each verdict | my staff know what action to take immediately |
| US-13 | developer | call a documented REST API for analysis | I can integrate TextShield into other tools |
| US-14 | quality engineer | run an automated test suite that covers every module | I can verify the system after each change |
| US-15 | user | check service/model/RAG health from the dashboard or API | I can confirm the system is functioning before relying on it |
| US-16 | consumer | receive a HAM verdict with reassurance reasoning for legitimate messages | I don't lose trust over false alarms |
| US-17 | student | browse the knowledge base by category | I can study real scam patterns and safety guidance |
| US-18 | privacy officer | confirm that no third-party service receives message content | I can approve deployment in a sensitive environment |
| US-19 | developer | understand fallback behavior (missing model/RAG/LLM) from docs | I can operate the system under degraded conditions |
| US-20 | end user | see which model version made my verdict | I can track model changes over time |

---

# 15. Use Cases

### UC-01 Analyze an SMS message
- **Actor:** End user (via UI or API client)
- **Preconditions:** Application running; model artifacts present.
- **Flow:** (1) User enters/pastes SMS text. (2) System normalizes and redacts content. (3) System extracts entities and URLs. (4) Classifier produces label + confidence. (5) Indicators and URL analyses run. (6) RAG retrieves top-k evidence. (7) Risk engine computes level + factors. (8) Explanation surface is generated. (9) Optional history record stored. (10) Structured result returned/rendered.
- **Postconditions:** Response contains classification, confidence, risk level, indicators, evidence, explanation, recommendation, `message_type`, and `rag_status`.
- **Alternate flows:** (A) Empty input → validation error 422. (B) Model missing → 503 with guidance message. (C) Index missing → analysis completes with `rag_status.ready=false` and no evidence.

### UC-02 Analyze a structured email
- **Actor:** End user
- **Flow:** User provides subject, sender, body (optionally raw email). System combines fields, detects raw-email markers when provided, extracts subject/sender/body if parsed, then proceeds as UC-01 from step 3.
- **Postconditions:** Same as UC-01 with `message_type = "email"`.

### UC-03 Auto-detect a pasted raw email in the text box
- **Actor:** End user
- **Flow:** User pastes a header-prefixed email into the generic text tab. System detects header markers in the first lines, upgrades the message type to email, extracts subject/sender/body, and runs the email analysis path.
- **Postconditions:** Analysis treats the content as an email; fields are visible in the result.
- **Alternate flow:** Content lacks header markers → treated as plain text as usual.

### UC-04 Inspect verdict evidence
- **Actor:** User, researcher, analyst
- **Flow:** From any analysis result, user expands the evidence section: matched indicators with severity/category/evidence excerpt; URL findings; retrieved knowledge chunks with source documents and categories; risk factors with reasoning.
- **Postconditions:** Every piece of evidence shown is traceable to the message or a real knowledge document.

### UC-05 Review history
- **Actor:** User
- **Flow:** User opens History page; system lists records with verdict/risk/timestamp (content redacted or hashed per settings); user filters, paginates, and may delete single records or all records; system also shows summary totals.
- **Postconditions:** History reflects the current store; deletions are honored.

### UC-06 Browse and rebuild knowledge base
- **Actor:** Knowledge curator, admin
- **Flow:** User opens Knowledge Base page; system lists categories with document and chunk counts; user triggers rebuild; system re-ingests all documents, re-embeds chunks, replaces the index, reports updated counts, and invalidates cached status.
- **Postconditions:** Index matches current documents; counts and build time updated.

### UC-07 View analytics
- **Actor:** Manager, admin
- **Flow:** User opens Analytics; system aggregates history into volume, verdict mix, risk distribution, average confidence, top indicators, top risk factors, and model info; charts render locally.
- **Postconditions:** Aggregates reflect stored history up to the present; page works without network access to CDNs.

### UC-08 Check service health
- **Actor:** Operator, developer
- **Flow:** User calls `GET /api/health` (or opens About); system reports model readiness, RAG readiness, vector backend, embedding provider, LLM provider/model availability, and history row count.
- **Postconditions:** Status flags enable quick triage of degraded deployments.

### UC-09 Retrain the model
- **Actor:** ML engineer
- **Flow:** Engineer runs the training script (after preparing dataset). System preprocesses corpus, builds TF-IDF features, evaluates candidate algorithms with cross-validation, selects the best (accuracy/F1 trade-off), calibrates probabilities, persists artifacts plus metadata and evaluation report.
- **Postconditions:** New artifacts are loadable at runtime; metadata reflects the new build.

### UC-10 Analyze via REST API
- **Actor:** Developer/integrator
- **Flow:** Client posts an `AnalyzeRequest` JSON; system executes UC-01 pipeline; client receives the structured analysis JSON; on validation failure or unavailability, machine-readable errors return.
- **Postconditions:** Response conforms to the documented schema; errors are structured.

### UC-11 Obtain an explanation when no LLM is configured
- **Actor:** Any user
- **Flow:** User analyzes a message while `LLM_MODEL` is empty/unset. System generates a deterministic, template-based explanation covering all six components and labels its source as `template`.
- **Postconditions:** Explanation present and clearly sourced; no external call made.

### UC-12 Evaluate model quality
- **Actor:** ML engineer, researcher
- **Flow:** Engineer runs the evaluation script on the held-out test set; system reports accuracy, precision/recall/F1 (per class and weighted), confusion matrix, calibration metrics, and saves the report.
- **Postconditions:** Report persisted and referenced in model metadata; verdicts reproducible.

---

# 16. AI Requirements

### AI-01 Semantic understanding
- Parse the message into its communicative structure (sender role, recipient, topic, tone, proposition).
- Produce meaning representations that treat paraphrase-equivalent scam phrasings consistently.
- **Acceptable approach:** normalized text + embeddings + structured indicator features.

### AI-02 Intent detection
- Assign an intent class: `credential_request`, `money_transfer`, `download_install`, `personal_data`, `prize_claim`, `confirmation_request`, `engagement`, `other`.
- Intent output must be **machine-readable** and included in the response.

### AI-03 Behavior analysis
- Detect social-engineering behaviors with severity and category tags (urgency, impersonation, bait, pressure, channel bypass).
- Behavior signals must be **explanatory**: each maps to evidence text in the message.

### AI-04 Context detection
- Use message structure (email fields, threading cues, sender signals) as context alongside body content.
- Support the raw-email auto-detection upgrade path (text → email) so context is never missed due to input-format assumptions.

### AI-05 Embedding generation
- Provide a local sentence-transformer for message and document embedding.
- Provide a deterministic fallback embedding provider so the RAG path is not single-point-of-failure.
- Embedding calls must be **local by default** with no third-party transmission.

### AI-06 Similarity search
- Given an embedded message, retrieve the most semantically similar knowledge chunks (cosine similarity over the vector index).
- Similarity must tolerate **lexical paraphrase** (different words, same meaning).

### AI-07 Evidence ranking
- Return top-k evidence ordered by relevance, each with source document, category, and chunk text.
- Evidence quality (relevance) must be auditable: the score that ordered the results is exposed or derivable.

### AI-08 Decision support
- Combine classifier probability, indicator severities, URL findings, and retrieval results into a single risk decision through documented rules (the risk engine).
- Decision logic must be **rule-transparent**, not a black box; factors enumerated per verdict.

### AI-09 Confidence estimation
- Provide calibrated confidence (probability) for the SPAM/HAM verdict via probability calibration (e.g., sigmoid/isotonic) on validation data.
- Report calibration quality (ECE/Brier) in the evaluation report.

### AI-10 Risk estimation
- Map combined signals to LOW/MEDIUM/HIGH/CRITICAL/UNCERTAIN with per-verdict factor justification.

### AI-11 Explainable AI
- Every verdict satisfies the explanation surface of Section 17 automatically.
- Explanation sources are labeled (template vs LLM); LLM output is constrained to the retrieved evidence + findings (no ungrounded claims).

---

# 17. Explainability Requirements

Every decision must answer the following six questions; **no verdict may be delivered without all six**:

| # | Requirement | Definition | Success check |
|---|---|---|---|
| EX-01 | What the message means | Plain-language restatement of the message's claim/offer/request | Restatement is faithful and includes the requested action |
| EX-02 | Why it is suspicious | Concrete reasons: matched indicators (with severity), URL risks, sender/entity mismatches, retrieved scam-pattern matches | Every suspicious claim maps to a visible evidence item |
| EX-03 | Why it may be legitimate | Counter-considerations: benign indicators, absence of risk behaviors, HAM-like features, legitimate-language patterns | Balanced reasoning present in every explanation |
| EX-04 | Evidence used | List of exactly what was used: classifier output, each indicator (category/severity/evidence), URL findings, retrieved knowledge chunks (source/category/text) | Evidence set equals the set shown in the response payload |
| EX-05 | Reasoning process | A summary of how evidence combined into the verdict and risk level (which factors were decisive) | Reasoning is consistent with the risk engine's documented rules |
| EX-06 | Recommendation | Concrete next step appropriate to the risk level (e.g., do-not-click/do-not-reply/report; or confirm via trusted channel) | Recommendation consistent with verdict and evidence |
| EX-07 | Source labeling | Explanation provenance (`template` or `llm`) and model/RAG version metadata visible | Provenance is truthful and documented |

Additional rules:
1. **Groundedness:** LLM-generated explanations must be constrained to retrieved evidence and indicator findings; no new external claims.
2. **Determinism:** With the same input and configuration, template explanations are byte-identical.
3. **No-expert bias:** Language must be comprehensible by a lay reader; glossary terms link to definitions.

---

# 18. Knowledge Base Requirements

## 18.1 Purpose and governance

The knowledge base is the authoritative, curated source of cybersecurity knowledge that grounds all RAG retrieval. Content must be **accurate, current, categorized, and traceable** (every document has a category and a filename-identifiable topic).

## 18.2 Required categories

| Category | Purpose | Example topics |
|---|---|---|
| Banking scams | Fraud targeting financial accounts | Account-blocked scams, fake payments, KYC verification scams |
| Email scams | Social engineering delivered by email | Invoice scams, account-verification scams, executive-impersonation briefs |
| SMS scams | Mobile-channel fraud | OTP scams, delivery scams, lottery/prize scams |
| Job scams | Employment-related fraud | Fake work-from-home offers, recruiter impersonation |
| Loan scams | Credit/loan fraud | Advance-fee loans, fake lenders |
| Investment scams | Financial-investment fraud | Crypto scams, guaranteed-return offers |
| Phishing | Credential and brand attacks | Brand impersonation, credential phishing |
| Spam patterns | Behavioral/linguistic patterns | Urgency tactics, promotional language, URL tactics, social engineering |
| Legitimate communication | Benign pattern reference | How legitimate banks/couriers/jobs typically communicate |
| Safety guidelines | User protective guidance | Safe URL checking, protecting yourself, what to do if scammed |
| Examples | Instructional case material | Annotated spam examples, annotated ham examples |
| Reference material | Foundational definitions | Phishing terminology, risk-level definitions, indicator catalog |

## 18.3 Content requirements

- Each document: title-equivalent filename, markdown structure, category membership, human-readable guidance.
- Documents suited to chunking: chunk boundaries must not split semantic units mid-sentence (deterministic chunker with overlap).
- The index must record per-document attribution so every retrieved chunk cites its source file and category.

## 18.4 Quality gates

- **Accuracy:** content reviewed against recognized threat reporting (see Section 30 references).
- **Freshness:** rebuild procedure exists; index records build timestamp; stale-index warnings surfaced in status.
- **Non-harm:** safety guidelines must not instruct users to click/reply to suspected scams.

---

# 19. Retrieval Requirements

## 19.1 Purpose of RAG in TextShield

Retrieval-Augmented Generation supplies the analysis pipeline with **relevant, cited knowledge at inference time**. Its purpose is threefold: (a) to ground verdicts in curated knowledge rather than model memory alone; (b) to make the system **extensible without retraining** — new attack documentation becomes retrievable the moment the index is rebuilt; (c) to produce **explainable connections**: "this message resembles the documented *account-blocked scam* pattern (source: banking_scams/account_blocked_scam.md)".

## 19.2 Why retrieval is necessary

1. **Long-tail coverage.** Novel or niche attack descriptions are rare in training corpora; retrieval surfaces them regardless.
2. **Countering hallucination.** The LLM composes explanations from retrieved text, so claims stay traceable.
3. **Maintainability.** Updating knowledge = editing documents + rebuilding the index, not retraining a model.
4. **User education.** Retrieved patterns teach users the *category* of the attack they faced.

## 19.3 How retrieved knowledge supports reasoning

- **Pattern confirmation:** retrieved chunks confirm or refute the hypothesis that the message matches a documented scam family.
- **Evidence binding:** each retrieved chunk binds reasoning to a real source (document, category, chunk text), satisfying EX-04.
- **Recommendation support:** safety-guideline chunks retrieved alongside scam-pattern chunks justify the recommended action.
- **Explanation quality:** the generator composes explanation paragraphs from retrieved chunks + indicator findings, keeping output grounded (EX-07).

## 19.4 Retrieval requirements

| ID | Requirement |
|---|---|
| RR-01 | Embed the normalized message with the active embedding provider before search. |
| RR-02 | Retrieve top-k (configurable, default documented) nearest chunks by cosine similarity. |
| RR-03 | Return metadata: source document, category, chunk index, similarity score. |
| RR-04 | Return **only real chunks**; never synthesize evidence (validated in tests). |
| RR-05 | Fallback: no index ⇒ `rag_status.ready=false` and empty evidence; analysis continues. |
| RR-06 | Cache store status for a short TTL; invalidate on rebuild. |
| RR-07 | Retrieval latency budget: ≤ 500 ms for the shipped knowledge base. |

---

# 20. Risk Assessment Requirements

## 20.1 Scale and semantics

| Level | Meaning | Typical composition | Recommended posture |
|---|---|---|---|
| **LOW** | Message shows no significant risk behaviors; benign characteristics dominate | HAM classification, high HAM confidence, no high-severity indicators, no risky URLs | Normal handling; verify only unusual requests with the known sender |
| **MEDIUM** | Ambiguous or mixed signals; some risk behaviors present without decisive malicious intent | Conflicting classifier/indicator signals; shortener or look-alike domains; mild urgency | Caution: verify sender through a trusted channel before acting |
| **HIGH** | Strong malicious indicators with credible attack patterns | SPAM classification with high confidence; multiple high-severity indicators; risky URLs; strong retrieved scam-pattern match | Do not click links, do not reply, do not provide information |
| **CRITICAL** | Evidence of an active attack (credential/money requests with impersonation and hyper-urgency) | SPAM, high confidence, credential/money-intent, brand impersonation, unsafe URLs, matching scam family | Do not act; report to the service provider / CERT; secure any potentially exposed accounts |
| **UNCERTAIN** | Components unavailable or signals insufficient for a confident verdict | Degraded operation (missing model/index) or balanced contradictory evidence | Treat with caution; re-run when components are restored |

## 20.2 Risk engine requirements

| ID | Requirement |
|---|---|
| RZ-01 | Every level is produced by documented rules combining: classifier label + confidence, indicator severities, URL findings, RAG evidence presence. |
| RZ-02 | Every verdict returns the list of **risk factors** that produced the level (transparency). |
| RZ-03 | CRITICAL requires a malicious-intent signal (credential/money/download request) *and* strong corroboration; it must never be granted on weak evidence. |
| RZ-04 | UNCERTAIN is reserved for degraded operation or irreconcilable evidence; it must never masquerade as a confident verdict. |
| RZ-05 | Risk computation is deterministic and unit-testable for every documented rule combination. |

---

# 21. Privacy Requirements

1. **Data minimization.** Only the message text required for analysis is processed; no metadata (location, contacts, device info) is collected.
2. **Redaction by default.** Phone numbers, email addresses, URLs, and monetary amounts are replaced with placeholders before storage.
3. **Hashed-content default.** Raw content is stored as SHA-256 digest unless the user explicitly opts in to readable storage per analysis.
4. **Local processing.** Embedding, retrieval, and (when configured) LLM inference are local; no message content leaves the machine by default. Any future remote LLM option requires an explicit opt-in flag in configuration.
5. **User control.** Users can delete a single history record or clear all history at any time.
6. **Transparency.** The About page and setup document state exactly: what is stored, in what form, for how long, and how it is deleted.
7. **No third-party sharing.** Analytics are computed locally from local history; no aggregated data is transmitted anywhere.
8. **Consent.** The first-run experience must inform users about history storage defaults and the opt-in switch.

---

# 22. Security Requirements

1. **Secrets hygiene.** No credentials, API keys, or tokens in source; all via environment variables; `.env` excluded from version control.
2. **Input integrity.** Validation of every API payload: types, lengths (max message length), allowed fields; oversized or malformed payloads rejected with 422.
3. **Output encoding.** All user-derived content rendered in pages is strictly HTML-escaped to prevent stored/reflected XSS.
4. **Path safety.** No user-controlled paths in filesystem operations; knowledge-base and model paths come from configuration only.
5. **Dependency hygiene.** Dependency versions pinned; dependency scanning and updates tracked in the release checklist.
6. **Localhost default binding** with explicit documentation for any LAN exposure; no implied network exposure.
7. **No eval/exec surfaces.** No user input ever reaches code-execution paths.
8. **Rate and abuse bounds.** History clear/rebuild actions bounded; analysis payload limits enforced.
9. **Error handling.** Internal errors logged server-side with context; clients receive generic-safe, structured errors (no stack traces).
10. **Model/history integrity.** Model artifacts are validated on load (exists/versioned); corrupt artifacts surface as clear 503, not crash-into-undefined-state.

---

# 23. Assumptions

| ID | Assumption |
|---|---|
| AS-01 | Messages are primarily **English-language** SMS and email text. |
| AS-02 | The system runs on **local, CPU-only hardware**; first-party GPU usage is not assumed. |
| AS-03 | The knowledge base content is **curated and reviewed** before ingestion; the system verifies retrieval, not content truth. |
| AS-04 | Users interact via the **web dashboard or the documented REST API**; no mail-protocol integration (SMTP/IMAP) is assumed in V2.0. |
| AS-05 | Training data is a **labeled SMS/email corpus** available under permissive terms; placement documented in the data guide. |
| AS-06 | Model inference is performant enough for interactive analysis (seconds, not minutes) with the shipped model sizes. |
| AS-07 | Embedding model(s) selected for V2.0 are installable from public, permissive model repositories; fallback exists if primary fails. |
| AS-08 | The local LLM (when configured) is reachable over localhost HTTP; lack of an LLM never blocks analysis (template mode). |
| AS-09 | Administrative operations (rebuild, retrain) are infrequent and operator-triggered, not continuously automated. |
| AS-10 | Content stored hashed by default is acceptable to users for audit purposes; readable storage is an explicit opt-in. |

---

# 24. Constraints

| ID | Constraint |
|---|---|
| CO-01 | **Local-first:** the core product must run without internet access or paid APIs (embedding, retrieval, classification, template explanations all local). |
| CO-02 | **Hardware budget:** must run on a mid-range laptop (reference: 8 GB RAM, CPU-only). |
| CO-03 | **Stack:** Python 3.10+ with the documented dependency set; web framework and ML stack chosen in later phases must honor NFRs. |
| CO-04 | **Explainability mandatory:** no configuration, mode, or failure path may produce a verdict lacking the full explanation surface. |
| CO-05 | **Determinism:** template explanations and risk-engine outputs are deterministic for fixed inputs. |
| CO-06 | **Corpus terms:** only datasets with permissive licensing may be bundled or downloaded by the prepare script. |
| CO-07 | **Offline installs:** first-run model/embedding downloads are documented; systems without network can use bundled alternatives (fallback embedding). |
| CO-08 | **Time and scope:** V2.0 is a single-developer/team academic-grade product; feature set bounded by Section 9. |
| CO-09 | **No external CDNs** in the web UI (fully self-hosted assets) so the dashboard works offline/LAN. |

---

# 25. Risks

## 25.1 Technical risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Embedding model download failure on first run | Medium | Analysis degraded to fallback embeddings | Fallback provider; cached model files; documented offline path |
| Vector-store corruption after interruption | Low | Retrieval unavailable | Rebuild-on-demand; status flags; startup validation |
| Classifier artifacts incompatible with new dependency versions | Medium | 503s at runtime | Pinned dependencies; artifact validation on load; retraining script |
| Template explanations become verbose/awkward with many indicators | Medium | Usability decline | Deterministic summarization rules; tests on edge cases |

## 25.2 Project risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Scope creep into mail-protocol integration or cloud work | High | Delays | Explicit Out-of-Scope list (Section 9.2); phase gates |
| Knowledge-base content quality/staleness | Medium | Wrong grounding | Curator review, category standards, build timestamping |
| Documentation drifts from implementation | Medium | Trust and usability suffer | Docs updated in same phase as code; doc tests where feasible |

## 25.3 AI risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM hallucination in explanations | Medium | Erroneous advice; trust loss | Grounding constraint to retrieved evidence; source labeling; template determinism; tests |
| Embedding retrieval misses relevant knowledge | Medium | Missing evidence | Top-k policy; category diversity in results; rebuild hygiene |
| Calibrated confidence drifts on distribution shift | Medium | Misleading probabilities | Evaluation report includes calibration metrics; retraining documented |
| False HAM on novel scams | Medium | Real harm to users | Risk engine requires corroboration for LOW on risky signals; explanations invite scrutiny |

## 25.4 Security risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Stored XSS through message content rendering | Low | User compromise | Strict output encoding; automated tests with payloads |
| Exposure beyond localhost with default config | Low | Message data exposure | Localhost default binding; documentation; startup warning on LAN bind |
| Prompt injection via analyzed message text (when LLM enabled) | Medium | LLM emits misleading content | LLM input framed as data-with-instructions-isolation; template mode unaffected |
| Dependency vulnerability | Medium | Unknown | Pinned versions; regular review; minimal dependency surface |

---

# 26. Success Metrics

| Metric | Definition | Target (V2.0) |
|---|---|---|
| Classification accuracy | Correct SPAM/HAM on the held-out test set | ≥ 95% |
| Spam F1-score | Harmonic mean of precision/recall for the spam class | ≥ 0.90 |
| Calibration quality | Expected Calibration Error (ECE) on test set | ≤ 0.10 (documented; report produced) |
| Evidence coverage | Share of test scam messages with ≥1 retrieved relevant chunk | ≥ 85% |
| Explanation completeness | Share of analysis responses containing all six components | 100% |
| Groundedness | Share of LLM-generated explanations whose claims trace to retrieved evidence or findings | ≥ 95% (sampled review protocol) |
| Graceful degradation | Successful analysis responses under missing RAG / LLM conditions | 100% (with status flags) |
| Pipeline latency | Median end-to-end analysis of a typical SMS | ≤ 5 s CPU-only |
| Test suite health | Automated tests passing on CI | 100% |
| Privacy defaults | Analyses stored hashed/redacted by default | 100% of default-config analyses |
| Rebuild integrity | Index counts equal source documents after rebuild | 100% |
| Documentation coverage | Sections 1–30 of PRD traced to implementation artifacts | 100% |

---

# 27. Future Scope

1. **Protocol integration:** IMAP/SMTP connectors, mail-server plugins, SMS gateway ingestion.
2. **Attachment and image analysis:** visual rendering checks, attachment metadata scanning, OCR-based text extraction for image payloads.
3. **Live URL intelligence:** reputation lookups (Safe Browsing-style), DNS/passive-DNS checks, certificate heuristics.
4. **Multi-language support:** language detection with per-language knowledge bases and models.
5. **Adaptive learning:** user-feedback loops (correct/incorrect) driving periodic fine-tuning while preserving explainability.
6. **Deployment scale:** containerization, multi-worker serving, cloud deployment with strict privacy controls.
7. **Regulatory compliance:** GDPR-style data governance features, export/erasure tooling, audit trails.
8. **Advanced XAI:** counterfactual explanations ("to be HAM, the message would need…"), saliency maps over tokens, uncertainty decomposition.
9. **Organizational features:** team workspaces, shared analytics, policy-driven risk thresholds, alert webhooks.
10. **Threat-intelligence integration:** ingestion of phishing feeds into the knowledge base with automated rebuild.
11. **Mobile and extension clients:** progressive web app, browser extension for mail clients.
12. **Benchmarking suite:** public evaluation harness against recognized spam/phishing corpora for reproducibility across versions.

---

# 28. Acceptance Criteria

Each criterion is independently verifiable; all must pass for V2.0 release.

| ID | Criterion | Verification method |
|---|---|---|
| AC-01 | A plain-text SMS submits and returns classification, confidence, risk level, indicators, evidence, explanation, recommendation, and `rag_status` | API integration test + UI manual check |
| AC-02 | A structured email (subject/sender/body) submits and returns `message_type="email"` | API test |
| AC-03 | A raw email with headers pasted into the text input is auto-detected and analyzed as email | API test + UI manual check |
| AC-04 | Empty/whitespace messages return 422 with a clear detail message | API test |
| AC-05 | With model artifacts present, health reports `status=ok`, `model_ready=true` | API test |
| AC-06 | With the vector index present, `rag_ready=true` and analysis returns retrieved chunks with source document/category | RAG test |
| AC-07 | With the index removed, analysis still returns a complete verdict with `rag_status.ready=false` | RAG test |
| AC-08 | With `LLM_MODEL` empty, explanations are produced by the template engine and labeled `template` | API test |
| AC-09 | All six explanation components (meaning, suspicion, legitimacy, evidence, reasoning, recommendation) are present in ~100% of tested responses | Response-schema test |
| AC-10 | Entities (phone/email/URL/money) are redacted to placeholders in normalized analysis output | Preprocessing test |
| AC-11 | History defaults: content stored hashed; single and bulk deletion work; stats reflect records | Database/API tests |
| AC-12 | Knowledge-base rebuild produces an index whose counts match source documents; cached status invalidated | KB API test |
| AC-13 | Analytics endpoint aggregates match stored history (volume, verdict mix, risk distribution) | API test |
| AC-14 | All dashboard pages (/, /history, /analytics, /knowledge-base, /about) return 200 and render without external CDN requests | HTTP checks + code inspection |
| AC-15 | The automated test suite passes 100% on a clean environment with one command | CI run |
| AC-16 | End-to-end latency for a typical SMS ≤ 5 s on reference hardware | Timed smoke test |
| AC-17 | Repeating the same analysis with template mode yields byte-identical explanations | Determinism test |
| AC-18 | No secrets in repository (scan for patterns; `.env` untracked); no default credentials anywhere | Repo scan + code review |
| AC-19 | Error responses never expose stack traces; 503 path returns actionable guidance | API tests + inspection |
| AC-20 | README, setup guide, architecture, ML pipeline, RAG pipeline, API reference, and PRD all exist and match implementation | Documentation review checklist |

---

# 29. Glossary

| Term | Definition |
|---|---|
| **SPAM** | Unsolicited, typically bulk, commercial or deceptive message content. |
| **HAM** | Legitimate, non-malicious message content (the binary opposite of spam in this system). |
| **Phishing** | An attack that impersonates a trusted entity to trick the victim into revealing credentials, data, or money. |
| **Social engineering** | Manipulation of human behavior and decision-making to achieve the attacker's goal. |
| **Semantic NLP** | Natural-language techniques that model *meaning*, not just surface word frequencies. |
| **Intent** | The sender's goal, e.g., credential harvesting, money movement, engagement. |
| **Behavior analysis** | Systematic evaluation of message behaviors (urgency, impersonation, bait) as signals. |
| **Embedding** | Dense vector representation of text where semantically similar texts are geometrically close. |
| **Sentence-transformer** | A transformer model fine-tuned to produce sentence-level embeddings. |
| **Vector store / vector database** | A system indexing embeddings for similarity search. |
| **chromadb** | The local, embeddable vector database used as the vector-store backend. |
| **RAG (Retrieval-Augmented Generation)** | A technique in which generation is grounded in retrieval: retrieve relevant knowledge, then compose an answer over it. |
| **Chunk** | A delimited unit of a knowledge document stored and embedded in the index. |
| **Cosine similarity** | A measure of directional similarity between two vectors, used for embedding search. |
| **LLM (Large Language Model)** | A language model capable of fluent generation; used here for explanation synthesis when configured. |
| **Template engine / template mode** | Deterministic rule-based explanation generation used when no LLM is available. |
| **Calibration** | Adjustment of predicted probabilities so that a stated 90% confidence is correct ~90% of the time. |
| **TF-IDF** | Term frequency–inverse document frequency weighting; classical text-feature scheme. |
| **Naive Bayes** | Probabilistic classifier assuming token independence. |
| **SVM / Linear SVM** | Support vector machine with a linear kernel; a strong classical text classifier. |
| **Logistic Regression** | Linear model producing calibrated class probabilities. |
| **Classifier** | The component that outputs the SPAM/HAM label and confidence. |
| **Indicator** | A rule-based finding with severity, category, and evidence excerpt (e.g., "urgency language"). |
| **Risk engine / decision engine** | The component that combines all signals into a risk level plus factors. |
| **Risk level** | LOW / MEDIUM / HIGH / CRITICAL / UNCERTAIN severity classification. |
| **Confidence** | Calibrated probability attached to the label. |
| **Explainability / XAI** | The property that every decision exposes its evidence and reasoning. |
| **Grounding** | The property that claims are traceable to retrieved or extracted evidence. |
| **Hallucination** | Generated content not supported by evidence (must be prevented in explanations). |
| **Redaction** | Replacing sensitive entities with placeholders before storage. |
| **SHA-256** | Cryptographic hash used to store content verifiably without readable exposure. |
| **SQLite** | Embedded relational database used for local history storage. |
| **REST API** | HTTP-based programmatic interface (analyze, history, stats, health, knowledge base). |
| **Knowledge base** | The curated markdown document collection grounding RAG. |
| **Index rebuild** | Re-chunking and re-embedding the knowledge base into the vector store. |
| **Top-k retrieval** | Returning the k most similar items, where k is configurable. |
| **ECE (Expected Calibration Error)** | Metric quantifying the gap between predicted probabilities and observed frequencies. |
| **Brier score** | Mean squared error of probability predictions versus outcomes. |
| **Confusion matrix** | Table of true class vs predicted class counts. |
| **Precision / Recall / F1** | Standard classification metrics (per class and weighted). |
| **XSS** | Cross-site scripting; injection of malicious scripts into rendered pages (prevented by output encoding). |
| **OTP** | One-time password; a common SMS-fraud token. |
| **CERT** | Computer Emergency Response Team; incident-reporting authority. |
| **SPF/DKIM/DMARC** | Email sender-authentication standards referenced in background context. |

---

# 30. References

Academic and industry references to be cited in the final version (placeholders; full bibliography to be added during documentation phase):

1. S. Yerima and S. Sezer, "DroidFusion: A Novel and Scalable Android Malware Classifier," *Journal of Network and Computer Applications* — *placeholder for spam/phishing classification methodology comparisons*.
2. A. Aleroud and L. Zhou, "Phishing Environments, Techniques, and Countermeasures: A Survey," *Computers & Security* — *placeholder for phishing taxonomy and countermeasure survey*.
3. J. Pennington, R. Socher, and C. Manning, "GloVe: Global Vectors for Word Representation," *EMNLP 2014* — *placeholder for embedding background*.
4. J. Devlin et al., "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding," *NAACL 2019* — *placeholder for transformer/contextual representation background*.
5. N. Reimers and I. Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," *EMNLP 2019* — *placeholder for sentence-embedding system* (the architecture used by the primary embedding provider).
6. P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," *NeurIPS 2020* — *placeholder for RAG methodology*.
7. D. Wang, Q. Feng, et al., "A Survey on Large Language Model based Autonomous Agents" — *placeholder for LLM grounding/hallucination-mitigation survey*.
8. R. Caruana et al., "Model Compression" / G. Plumb et al., "Model Agnostic Supervised Local Explanations" — *placeholders for explainable-AI methodology background*.
9. G. Gupta, C. Sarma, and S. Sharma, "Phishing Suspicious Email Detection: An Evaluation of Classification Techniques," *Conference on Computational Intelligence* — *placeholder for classical classifier evaluation*.
10. S. Sheng et al., "Anti-Phishing Phil: The Design and Evaluation of a Game That Teaches People Not to Fall for Phish," *SOUPS 2007* — *placeholder for user-education and explainability rationale*.
11. "OpenAI GPT-4 Technical Report" / local-open-model white papers (Llama, Mistral) — *placeholders for LLM capability and local-deployment constraints*.
12. Google, "Safe Browsing" documentation — *placeholder for URL-reputation industry practice*.
13. OWASP, "Cross-Site Scripting Prevention Cheat Sheet" — *placeholder for XSS-prevention standards*.
14. NIST, "Glossary of Key Information Security Terms" (NISTIR 7298) — *placeholder for security terminology alignment*.
15. UCI Machine Learning Repository, "SMS Spam Collection" — *placeholder for open dataset licensing and citation*.
16. Enron Spam Datasets / TREC Spam Tracking — *placeholders for email-corpus references*.

*(Full bibliographic entries with authors, venues, years, DOIs, and access dates to be completed in the documentation phase before release.)*

---

## Document control

| Version | Date | Author | Change summary |
|---|---|---|---|
| 2.0 | TBD | TextShield Product/Engineering team | Initial complete PRD for Phase 1; defines foundation for all remaining phases |