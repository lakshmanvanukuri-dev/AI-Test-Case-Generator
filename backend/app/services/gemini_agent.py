import google.generativeai as genai
from app.core.config import settings

class GeminiAgent:
    def __init__(self):
        # Configure the Gemini API with the key from settings
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # Initialize the model
        # Using gemini-2.5-pro for advanced reasoning
        self.model = genai.GenerativeModel('gemini-2.5-pro')

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

    def generate_code(self, test_case: dict) -> str:
        """
        Generates a static Playwright script based on the test case steps.
        """
        steps_str = "\n".join([f"- {s}" for s in test_case.get('steps', [])])
        prompt = f"""
        You are a QA Automation Expert.
        Generate a Python Playwright script (using async_playwright) for this test case.
        
        Test Case: {test_case.get('title')}
        Steps:
        {steps_str}
        Expected Result: {test_case.get('expected_result')}
        
        Requirements:
        - Use 'page' variable assuming it's already created.
        - You MUST generate code for EVERY step listed above. Do not skip any steps.
        - Include an assertion at the end to verify the 'Expected Result'.
        - Add comments for each step.
        - Return ONLY the Python code (no markdown).
        - Do NOT include 'import' statements or 'async with' blocks, just the steps inside the function.
        """
        try:
            response = self.model.generate_content(prompt)
            print(f"DEBUG: Gemini Response: {response.text}") # Debug print
            code = response.text.replace("```python", "").replace("```", "").strip()
            if not code:
                return "# No code generated"
            return code
        except Exception as e:
            print(f"DEBUG: Error: {e}") # Debug print
            return f"# Error generating code: {str(e)}"
