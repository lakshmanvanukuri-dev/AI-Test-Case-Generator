import google.generativeai as genai
from app.core.config import settings

class GeminiAgent:
    def __init__(self):
        # Configure the Gemini API with the key from settings
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # Initialize the model
        # Using gemini-2.5-flash-lite as requested
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

    def generate_test_cases(self, user_story: str, acceptance_criteria: str) -> str:
        """
        Generates test cases based on the provided user story and acceptance criteria.
        """
        
        prompt = f"""
        You are an expert Quality Assurance Engineer.
        
        Task: Generate detailed test cases for the following User Story.
        
        User Story:
        {user_story}
        
        Acceptance Criteria:
        {acceptance_criteria}
        
        Output Format:
        Provide the response in a structured JSON format with the following fields for each test case:
        - id: A unique identifier (e.g., TC-001)
        - title: A concise title for the test case
        - type: 'Positive' or 'Negative'
        - steps: A list of steps to execute
        - expected_result: The expected outcome
        
        Do not include any markdown formatting or explanations outside the JSON.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception:
            return "[]"
