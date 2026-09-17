#!/usr/bin/env bash
# cURL examples — TextShield v2.2
BASE=http://127.0.0.1:8000

# Single analyze
curl -s -X POST $BASE/api/analyze -H "Content-Type: application/json" -d '{"text":"Urgent: verify http://evil.top"}' | jq

# Health
curl -s $BASE/api/health | jq
curl -s $BASE/api/liveness | jq
curl -s $BASE/api/version | jq

# IOC extract
curl -s -X POST $BASE/api/v2/ioc/extract -H "Content-Type: application/json" -d '{"text":"Visit http://evil.com IP 203.0.113.1"}' | jq

# Threat providers
curl -s $BASE/api/v2/threat/providers/openphish | jq

# Batch (enterprise)
curl -s -X POST $BASE/api/v2/batch -H "Content-Type: application/json" -d '{"texts":["hello","win prize http://bit.ly/abc"]}' | jq
