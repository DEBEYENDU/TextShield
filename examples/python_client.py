"""Python SDK example — TextShield v2.2"""
import requests

BASE = "http://127.0.0.1:8000"
API_KEY = ""  # set if production

def analyze(text: str):
    r = requests.post(f"{BASE}/api/analyze", json={"text": text}, headers={"X-API-Key": API_KEY} if API_KEY else {})
    print(r.json())

if __name__ == "__main__":
    analyze("Congratulations! You won $1000. Click http://bit.ly/abc to claim")
    analyze("Meeting notes for tomorrow at 10am")
