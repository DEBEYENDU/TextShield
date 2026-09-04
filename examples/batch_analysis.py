"""Batch analysis example — POST /api/v2/batch with polling"""
import requests, time
BASE="http://127.0.0.1:8000"
texts = ["Legit meeting notes", "Win money! http://bit.ly/xyz", "Your OTP is 123456"]
r = requests.post(f"{BASE}/api/v2/batch", json={"texts": texts})
print("job", r.json())
# poll history or job status if implemented
time.sleep(1)
print(requests.get(f"{BASE}/api/history?limit=5").json())
