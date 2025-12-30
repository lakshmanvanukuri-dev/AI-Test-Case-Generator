import requests
import json

url = "http://localhost:8004/api/v1/chat"
payload = {
    "message": "Run on https://example.com",
    "test_case": {"steps": []}
}
headers = {"Content-Type": "application/json"}

print(f"Sending request to {url}...")
try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
