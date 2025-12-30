import requests

url = "http://localhost:8003/api/v1/generate-code"
data = {
    "test_case": {
        "title": "Open google",
        "steps": ["Open google.com", "Search for Playwright"]
    }
}

try:
    # Check root
    response = requests.get("http://localhost:8003/")
    print(f"Root Status: {response.status_code}")
    print(f"Root Response: {response.json()}")

    # Check docs
    response = requests.get("http://localhost:8003/docs")
    print(f"Docs Status: {response.status_code}")

    # Check generate
    url_gen = "http://localhost:8003/api/v1/generate"
    data_gen = {
        "user_story": "As a user I want to login",
        "acceptance_criteria": "Valid credentials work"
    }
    response = requests.post(url_gen, json=data_gen)
    print(f"Generate Status: {response.status_code}")

    # Check test
    response = requests.get("http://localhost:8003/api/v1/test")
    print(f"Test Endpoint Status: {response.status_code}")

    # Check generate-code
    url = "http://localhost:8003/api/v1/generate-code"
    response = requests.post(url, json=data)
    print(f"Generate Code Status: {response.status_code}")
    print(f"Generate Code Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
