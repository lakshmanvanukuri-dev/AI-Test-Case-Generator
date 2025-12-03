import requests
import json

url = "http://localhost:8000/api/v1/generate"
payload = {
    "user_story": "As a user I want to login",
    "acceptance_criteria": "Valid credentials should work"
}

try:
    print("Sending request...")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
