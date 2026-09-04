"""Webhook usage — register + test delivery"""
import requests
BASE="http://127.0.0.1:8000"
# register
r = requests.post(f"{BASE}/api/v2/webhooks", json={"event":"AnalysisStored","url":"https://example.com/hook","secret":"s3cret"})
print(r.json())
# trigger analysis will fire webhook via event_bus
requests.post(f"{BASE}/api/analyze", json={"text":"phishing http://evil.top"})
