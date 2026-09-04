# Benchmark Summary — v2.2.0

Source: `benchmarks/history.json` + `report.json` (20 iters).

| Target | Mean | Thr | Result |
|---|---|---|---|
| single_message | 42ms warm | 4000 | pass |
| batch 10 | 380ms | 8000 | pass |
| ioc_extraction | 8.2ms | 80 | pass |
| threat_lookup | 12.4ms | 200 | pass |
| cache | 0.85ms | 10 | pass |
| rag | 22.5ms | 200 | pass |
| ml | 9.8ms | 100 | pass |
| api | 18.3ms | 150 | pass |
| dashboard | 6.1ms | 150 | pass |

No regressions. See `docs/performance/Performance_Report.md`.
