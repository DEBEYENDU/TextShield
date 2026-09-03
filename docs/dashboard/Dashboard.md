# Threat Intelligence Dashboard & Security Analytics

## Architecture

The dashboard is built as a thin presentation layer on top of the existing TextShield analytics backend.

- **Frontend**: Jinja2 templates served by FastAPI, using Chart.js for client-side visualisation.
- **Backend**: `app/analytics/` modules provide aggregated statistics, provider status, threat history, cache analytics, and execution metrics.

### Backend Modules

| Module | Responsibility |
|---|---|
| `dashboards.py` | Top-level dashboard summary, provider status, cache stats, execution metrics, confidence breakdown |
| `metrics.py` | `MetricsEngine`, `MetricsRecord`, `MetricsSummary`, `MetricKeys` — execution pipeline metrics |
| `history.py` | `AnalysisHistory`, `HistoryService`, `get_dashboard_history`, `get_severity_distribution` |
| `summaries.py` | `get_threat_score_distribution`, `get_provider_comparison` |

### Frontend Structure

```
frontend/
├── src/
│   ├── pages/
│   │   └── ThreatDashboard/
│   │       └── dashboard.html
│   └── components/
│       ├── ThreatSummary/
│       ├── IOCExplorer/
│       ├── EvidenceTimeline/
│       ├── ThreatGraph/
│       ├── ProviderStatus/
│       ├── ProviderComparison/
│       ├── ThreatHeatmap/
│       ├── CacheStatistics/
│       ├── ExecutionMetrics/
│       ├── RecentThreats/
│       ├── ThreatHistory/
│       └── ConfidenceBreakdown/
├── templates/
│   └── base.html
└── static/
```

## API Endpoints

All endpoints are prefixed with `/api/v2/dashboard`.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/summary` | Overall dashboard summary |
| GET | `/providers` | Per-provider health & quota status |
| GET | `/history` | Searchable threat history (paginated, filterable) |
| GET | `/history/filters` | Available filter options |
| GET | `/cache` | Cache analytics |
| GET | `/metrics` | Execution pipeline metrics |
| GET | `/threats` | Recent threats (top 10) |
| GET | `/score-distribution` | Threat score distribution for charts |
| GET | `/provider-comparison/{ioc_value}` | Compare provider responses for an IOC |

### Example: Dashboard Summary

```bash
curl -X GET http://localhost:8000/api/v2/dashboard/summary
```

Response:

```json
{
    "total_analyses": 1247,
    "threat_score_distribution": {
        "low": 520,
        "medium": 410,
        "high": 210,
        "critical": 107
    },
    "average_confidence": 0.73,
    "high_risk_detections": 317,
    "provider_health": {
        "google_safe_browsing": {"status": "healthy", "latency_ms": 120},
        "virustotal": {"status": "healthy", "latency_ms": 210}
    }
}
```

## Dashboard Sections

### 1. Threat Overview
- Total analyses
- Threat score distribution (Low/Medium/High/Critical)
- High-risk detections
- Average confidence
- Provider health summary

### 2. IOC Explorer
- Search by URL, domain, email, phone, IP, hash
- Display: history, threat profile, provider results, evidence, timeline

### 3. Evidence Timeline
- Visualises the full chain: message → IOC extraction → cache lookup → provider response → aggregation → evidence integration → decision

### 4. Threat Graph
- Interactive graph showing relationships between messages, indicators, providers, evidence, and threat profiles

### 5. Provider Status
- Health, latency, success rate, failures, quota usage, circuit breaker state

### 6. Provider Comparison
- Compare provider responses for the same IOC
- Highlights agreement, disagreement, missing responses, confidence

### 7. Threat Heatmap
- Threat volume, severity distribution, confidence distribution, provider coverage

### 8. Cache Analytics
- Cache size, hit/miss ratio, TTL distribution, evictions, top queried IOCs

### 9. Execution Metrics
- Average lookup time, concurrency, queue depth, retries, timeouts, requests per second

### 10. Threat History
- Searchable, filterable history (date, IOC type, threat score, provider, severity)
- Pagination support

### 11. Confidence Breakdown
- Breakdown of confidence contributions: Threat Intelligence, ML, LLM, Rules, RAG, Semantic Analysis, Intent Analysis

## Charts & Visualisation

Charts are rendered with **Chart.js** loaded from CDN. Each chart component is lazy-loaded:

- **Bar charts**: threat score distribution, severity distribution
- **Line charts**: evidence timeline, execution metrics over time
- **Doughnut charts**: confidence breakdown, provider distribution
- **Heatmaps**: threat volume by time window

## Configuration

Dashboard behaviour is configured via the same settings module used by the rest of TextShield:

- `DASHBOARD_PAGE_SIZE` – default page size for history (default: 50)
- `DASHBOARD_MAX_PAGE_SIZE` – maximum allowed page size (default: 200)
- `DASHBOARD_REFRESH_INTERVAL` – optional auto-refresh interval in seconds

## Known Limitations

- Frontend is currently server-rendered (Jinja2); a full SPA is planned for a future milestone.
- Mock data is used where real database/cache queries are not yet implemented; these will be replaced as the underlying storage layers mature.
- Real-time updates require a WebSocket layer (future milestone).

## Remaining RFC Dependencies

- Additional provider integrations (OpenPhish, PhishTank, URLhaus, AbuseIPDB)
- Threat aggregation / timeline
- Decision Engine integration
- Full SPA frontend (React/Vue)
- WebSocket-based real-time updates