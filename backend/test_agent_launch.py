import requests
import json

url = "http://127.0.0.1:8004/api/v1/run-agent"
headers = {"Content-Type": "application/json"}
data = {
    "test_steps": ["Go to https://example.com"],
    "user_context": "Go to https://example.com"
}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
