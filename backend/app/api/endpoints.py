from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from app.services.gemini_agent import GeminiAgent
from app.services.jira_service import JiraService
from app.services.playwright_agent import AutonomousPlaywrightAgent
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint working"}

agent = GeminiAgent()
jira_service = JiraService()
playwright_agent = AutonomousPlaywrightAgent()

class TestCaseRequest(BaseModel):
    user_story: str
    acceptance_criteria: str

class JiraExportRequest(BaseModel):
    project_key: str
    # Explicitly accept BOTH formats to be 100% safe
    parent_key: Optional[str] = None
    parentKey: Optional[str] = None 
    test_cases: list
    
    class Config:
        populate_by_name = True

class TestCaseResponse(BaseModel):
    test_cases: list

class RunAgentRequest(BaseModel):
    test_steps: list
    user_context: str

class ChatRequest(BaseModel):
    message: str
    test_case: dict

class CodeGenRequest(BaseModel):
    test_case: dict

@router.post("/generate-code")
async def generate_code_endpoint(request: CodeGenRequest):
    """
    Generates the static Playwright code for preview.
    """
    try:
        code = agent.generate_code(request.test_case)
        return {"code": code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_agent(request: ChatRequest):
    """
    Conversational endpoint for the agent.
    """
    try:
        response = await playwright_agent.chat(request.message, request.test_case)
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run-agent")
async def run_autonomous_agent(request: RunAgentRequest):
    """
    Triggers the autonomous agent to execute steps on a live browser.
    """
    try:
        # Pass both steps and context, but the agent mainly needs the context (prompt)
        results = await playwright_agent.run_test_case(request.test_steps, request.user_context)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    # LOGIC: Resolve parent key from either field
    final_parent_key = request.parent_key or request.parentKey
    
    logger.info(f"Received export request. Project: {request.project_key}, Parent: {final_parent_key}")
    
    results = []
    for tc in request.test_cases:
        description = f"**Type:** {tc.get('type')}\n\n**Steps:**\n"
        for step in tc.get('steps', []):
            description += f"- {step}\n"
        description += f"\n**Expected Result:**\n{tc.get('expected_result')}"

        result = jira_service.create_test_case(
            project_key=request.project_key,
            summary=tc.get('title'),
            description=description,
            parent_key=final_parent_key
        )
        results.append(result)
    
    return {"results": results}
