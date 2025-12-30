import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key found: {api_key[:5]}..." if api_key else "API Key NOT found")

if api_key:
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content("Hello, are you working?")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
