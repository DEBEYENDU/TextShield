# Architecture Diagrams — TextShield v2.2

All diagrams use Mermaid (rendered on GitHub / `docsify`).

## Overall Architecture
```mermaid
graph TB
  User[User Text/SMS/Email] --> Main[app/main.py create_app]
  Main --> Middleware[Middleware: RequestID/Security/RateLimit/Logging]
  Middleware --> Router[FastAPI Routers: analysis/history/system/v2]
  Router --> Services[Services: analysis_service + risk_engine]
  Services --> ML[ML Classifier + Indicators + URL Analyzer]
  Services --> RAG[RAG: ChromaDB + Embeddings]
  Services --> TI[Threat Intelligence Platform]
  TI --> Cache[Threat Cache]
  TI --> Providers[Providers x6]
  TI --> Agg[Aggregation]
  Evidence[Evidence Engine] --> Decision[Decision Engine]
  ML --> Evidence
  RAG --> Evidence
  Agg --> Evidence
  Decision --> DB[(SQLite WAL)]
  Decision --> Dashboard[Threat Dashboard + Analytics]
```

## Request Flow
```mermaid
sequenceDiagram
  participant C as Client
  participant F as FastAPI
  participant A as AnalysisService
  participant M as ML
  participant R as RAG
  participant T as Threat
  C->>F: POST /api/analyze {text}
  F->>A: analyze()
  A->>M: preprocess → TF-IDF → predict
  A->>T: IOCEngine.extract + Cache lookup → Providers (async) → Aggregate
  A->>R: retriever.retrieve()
  A->>A: risk_engine + EvidenceEngine.merge
  A-->>F: {classification, confidence, risk, evidence}
  F-->>C: JSON envelope + X-Request-ID
```

## Threat Intelligence Flow
```mermaid
graph LR
  Text-->IOC[IOCEngine]
  IOC-->Cache[CacheManager]
  Cache-->|miss|Coord[ThreatCoordinator]
  Coord-->Sched[Scheduler]
  Sched-->Disp[Dispatcher]
  Disp-->Exec[Executor - semaphore 10]
  Exec-->GSB[GoogleSafeBrowsing]
  Exec-->VT[VirusTotal]
  Exec-->OP[OpenPhish]
  Exec-->PT[PhishTank]
  Exec-->UH[URLhaus]
  Exec-->AB[AbuseIPDB]
  GSB-->CB[CircuitBreaker]
  Providers-->Agg[Aggregation Weighting+Fusion]
  Agg-->Profile[ThreatProfile]
```

## Evidence Flow
```mermaid
graph TB
  Msg[Message] --> Sources[7 Sources]
  Sources --> ML[Hybrid ML]
  Sources --> TI[Threat Intel]
  Sources --> LLM[LLM]
  Sources --> RAG[RAG]
  Sources --> Rules[Rules]
  Sources --> Sem[Semantic]
  Sources --> Intent[Intent]
  ML --> Registry[EvidenceRegistry]
  TI --> Registry
  Registry --> Graph[EvidenceGraph adjacency]
  Graph --> Merger[Merger + Conflict Detection]
  Merger --> Confidence[Confidence 5-factor]
  Confidence --> Explanation[Human Summary]
```

## RAG Pipeline
```mermaid
graph LR
  Docs[knowledge_base/*.md] --> Chunker[Chunk 700 overlap]
  Chunker --> Embed[Embed all-MiniLM-L6-v2 / hashing]
  Embed --> Store[(ChromaDB / numpy vector_db)]
  Query[User text] --> QEmbed[Embed Query]
  QEmbed --> Search[Top-K 4 search]
  Search --> Context[Context + scores]
  Context --> LLM[LLM or template]
  LLM --> Explanation
```

## Plugin Architecture
```mermaid
graph TB
  Registry[PluginRegistry]
  PluginA[MyPlugin initialize/metadata/capabilities/health]
  PluginB[OtherPlugin]
  Events[EventBus MessageReceived/AnalysisStored]
  Registry --> PluginA
  Registry --> PluginB
  PluginA --> Events
  Events --> Webhooks[Webhooks POST with retries/signing]
```

## Provider Architecture
```mermaid
graph TB
  IProvider[IThreatProvider ABC]
  GSB[GoogleSafeBrowsing config/client/mapper/models/validator/provider]
  VT[VirusTotal ...]
  OP[OpenPhish ...]
  PT[PhishTank ...]
  UH[URLhaus ...]
  AB[AbuseIPDB ...]
  IProvider --> GSB
  IProvider --> VT
  IProvider --> OP
  IProvider --> PT
  IProvider --> UH
  IProvider --> AB
  GSB --> Client[Client retry/rate/cache]
  Client --> Mapper[Response->ThreatIndicator->ThreatEvidence]
  Mapper --> Registry
```

## Deployment Diagram
```mermaid
graph TB
  LB[NGINX/ALB TLS + WAF] --> FastAPI[Uvicorn FastAPI]
  FastAPI --> SQLite[(SQLite WAL textshield.db)]
  FastAPI --> VectorDB[(vector_db)]
  FastAPI --> Models[(models/joblib)]
  FastAPI --> Logs[logs 5MBx5 -> ELK]
  FastAPI --> ProvidersAPI[External APIs: GSB/VT/Abuse.ch/PhishTank]
  K8s[K8s liveness/readiness probes] --> FastAPI
  CI[GitHub Actions black/ruff/mypy/pytest/benchmark/pip-audit]
```
