from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.gemini_agent import GeminiAgent
from app.services.jira_service import JiraService
import json

router = APIRouter()
agent = GeminiAgent()
jira_service = JiraService()

class TestCaseRequest(BaseModel):
    user_story: str
    acceptance_criteria: str

class JiraExportRequest(BaseModel):
    project_key: str
    parent_key: str = None
    test_cases: list

class TestCaseResponse(BaseModel):
    test_cases: list

@router.post("/generate", response_model=TestCaseResponse)
async def generate_test_cases(request: TestCaseRequest):
    """
    Endpoint to generate test cases from a user story.
    """
    try:
        # Call the AI agent to generate test cases
        result_text = agent.generate_test_cases(request.user_story, request.acceptance_criteria)
        
        # Improved cleaning: Find the JSON array
        try:
            start_index = result_text.find('[')
            end_index = result_text.rfind(']') + 1
            if start_index != -1 and end_index != -1:
                json_str = result_text[start_index:end_index]
                test_cases = json.loads(json_str)
            else:
                # Fallback to original cleaning if no brackets found
                cleaned_text = result_text.replace("```json", "").replace("```", "").strip()
                test_cases = json.loads(cleaned_text)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse AI response. The model might have returned invalid JSON.")
        
        return {"test_cases": test_cases}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export-to-jira")
async def export_to_jira(request: JiraExportRequest):
    """
    Endpoint to save generated test cases to Jira.
    """
    results = []
    for tc in request.test_cases:
        # Format the description
        description = f"**Type:** {tc.get('type')}\n\n**Steps:**\n"
        for step in tc.get('steps', []):
            description += f"- {step}\n"
        description += f"\n**Expected Result:**\n{tc.get('expected_result')}"

        # Create issue in Jira
        result = jira_service.create_test_case(
            project_key=request.project_key,
            summary=tc.get('title'),
            description=description,
            parent_key=request.parent_key
        )
        results.append(result)
    
    return {"results": results}
