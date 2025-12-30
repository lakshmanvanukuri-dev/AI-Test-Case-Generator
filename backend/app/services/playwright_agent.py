import json
import time
import traceback
import logging
import asyncio
import re
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Page, Browser, Playwright, expect
from app.services.gemini_agent import GeminiAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- GLOBAL STATE FOR PERSISTENT BROWSER ---
_browser_state: Dict[str, Any] = {
    "playwright": None,
    "browser": None,
    "context": None,
    "page": None,
    "active": False,
    "memory": {} 
}

class AutonomousPlaywrightAgent:
    def __init__(self):
        self.gemini = GeminiAgent()

    async def chat(self, user_message: str, test_case: dict):
        is_active = False
        if _browser_state.get("active"):
            is_active = True

        url_match = re.search(r'https?://[^\s]+', user_message)
        
        if url_match:
            logger.info(f"URL Detected: {url_match.group(0)}")
            # Reset memory on new URL
            _browser_state["memory"] = {} 
            results = await self.run_test_case(test_case.get('steps', []), user_message)
            return {"type": "result", "results": results}
        
        elif is_active:
            logger.info("Active session detected. Processing follow-up...")
            results = await self.run_test_case([user_message], user_message)
            return {"type": "result", "results": results}
            
        else:
            return {
                "type": "message", 
                "content": "I'm ready to run this test. Please provide the **Target URL** (e.g., 'Run on https://example.com')."
            }

    async def run_test_case(self, steps: List[str], user_context: str) -> List[Dict[str, Any]]:
        global _browser_state
        results = []
        
        try:
            # 1. Ensure Browser is Open
            if not _browser_state["active"] or not _browser_state["page"]:
                logger.info("Launching New Browser Session...")
                try:
                    p = await async_playwright().start()
                    # Launch with args to avoid bot detection and maximize
                    browser = await p.chromium.launch(
                        headless=False, 
                        slow_mo=1000,
                        channel="chrome",
                        args=["--start-maximized", "--window-size=1920,1080", "--disable-blink-features=AutomationControlled"]
                    )
                    # Viewport None is required for true maximization
                    context = await browser.new_context(viewport=None)
                    page = await context.new_page()
                    
                    # Fallback: Attempt to maximize via JS if the arg failed
                    try:
                        await page.evaluate("window.moveTo(0, 0); window.resizeTo(screen.availWidth, screen.availHeight);")
                    except Exception:
                        pass
                    
                    _browser_state["playwright"] = p
                    _browser_state["browser"] = browser
                    _browser_state["context"] = context
                    _browser_state["page"] = page
                    _browser_state["active"] = True
                    _browser_state["memory"] = {} # Initialize memory
                    logger.info("Browser Launched Successfully.")
                except Exception as e:
                    logger.error(f"Browser Launch Failed: {e}")
                    return [{"step": "Browser Launch", "status": "Failed", "error": str(e), "detail": "Could not start Chrome."}]
            else:
                logger.info("Reusing Existing Browser Session.")

            # 2. Handle Initial Navigation
            page = _browser_state["page"]
            if page.url == "about:blank":
                url_match = re.search(r'https?://[^\s]+', user_context)
                if url_match:
                    url = url_match.group(0)
                    logger.info(f"Navigating to: {url}")
                    try:
                        await page.goto(url)
                    except Exception as e:
                        results.append({"step": f"Navigate to {url}", "status": "Failed", "error": str(e)})

            # 3. Execute Steps
            for step in steps:
                # Always refresh page reference from global state (in case of tab switch)
                page = _browser_state["page"]
                step_desc = step if isinstance(step, str) else step.get("description", str(step))
                
                try:
                    await self._execute_step_with_retry(page, step_desc, user_context)
                    results.append({"step": step_desc, "status": "Success", "detail": "Executed successfully"})
                except Exception as e:
                    logger.error(f"Step Failed: {step_desc} | Error: {e}")
                    results.append({"step": step_desc, "status": "Failed", "error": str(e), "detail": str(e)})
                    # Stop execution on failure
                    break 

            return results

        except Exception as e:
            logger.error(f"Critical Session Error: {e}")
            return [{"step": "Session Error", "status": "Failed", "error": str(e), "detail": str(e)}]

    async def _execute_step_with_retry(self, page: Page, step_desc: str, user_context: str):
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                # Always use the current page object from global state
                current_page = _browser_state["page"]
                
                if attempt == 0:
                    logger.info(f"Executing Step: {step_desc}")
                    await self._execute_single_step(current_page, step_desc, user_context)
                else:
                    logger.warning(f"Attempt {attempt + 1} Failed. Initiating Self-Healing...")
                    
                    # Capture snapshot safely
                    try:
                        snapshot = await current_page.accessibility.snapshot()
                        logger.info("Accessibility Snapshot Captured.")
                    except Exception:
                        await asyncio.sleep(2)
                        snapshot = await current_page.accessibility.snapshot()

                    prompt = f"""
                    I am trying to execute this Playwright step: "{step_desc}"
                    Context: "{user_context}"
                    The previous attempt failed with: "{str(last_error)}"
                    
                    CURRENT MEMORY (Use these values if needed):
                    {json.dumps(_browser_state["memory"], indent=2)}

                    Here is the current accessibility tree (JSON):
                    {json.dumps(snapshot, indent=2)[:10000]} 
                    
                    TASK:
                    1. Analyze the tree.
                    2. If there is a popup/modal, close it.
                    3. Provide corrected Python Playwright (ASYNC) code.
                    4. Use `force=True` for difficult clicks.
                    5. Use `await` for all async calls.
                    
                    Only return the code.
                    """
                    
                    healing_code = self.gemini.model.generate_content(prompt).text.strip()
                    healing_code = healing_code.replace("```python", "").replace("```", "").strip()
                    
                    logger.info(f"Gemini Suggested Fix: {healing_code}")
                    await self._exec_code_safe(current_page, healing_code)
                
                return

            except Exception as e:
                last_error = e
                logger.error(f"Error on attempt {attempt + 1}: {e}")
                await asyncio.sleep(2)
        
        raise Exception(f"Failed after {max_retries} attempts. Last error: {last_error}")

    async def _execute_single_step(self, page: Page, step_desc: str, user_context: str):
        # Inject current memory into the prompt
        memory_str = json.dumps(_browser_state["memory"], indent=2)
        
        prompt = f"""
        Translate this test step into Python Playwright (ASYNC) code:
        "{step_desc}"
        
        Context: "{user_context}"
        
        CURRENT MEMORY (Variables created in previous steps):
        {memory_str}
        
        INSTRUCTIONS:
        1. **MEMORY**: If the step requires data (like a name) and it exists in MEMORY, USE IT.
        2. **NEW DATA**: If the step requires generating NEW random data, save it to `_memory`.
        3. **CREDENTIALS**: If the step requires a username/password:
           - First check if they are provided in the 'Context'.
           - If NOT provided, DO NOT generate random ones. Instead, assume standard demo credentials (e.g., Admin/admin123 for OrangeHRM) OR ask the user.
           - For OrangeHRM specifically, use 'Admin' and 'admin123' if no other credentials are found.
        4. **ROBUSTNESS**:
           - Use `await page.locator(...).click(force=True)` for buttons.
           - Use `await expect(...).to_be_visible(timeout=15000)` for verifications.
        
        Assume 'page', 'expect', and '_memory' are available.
        Just the action code.
        """
        
        code = self.gemini.model.generate_content(prompt).text.strip()
        code = code.replace("```python", "").replace("```", "").strip()
        await self._exec_code_safe(page, code)

    async def _exec_code_safe(self, page: Page, code: str):
        global _browser_state
        context = page.context
        initial_page_count = len(context.pages)
        
        # Pass the global memory dict to the exec scope so the AI can read/write to it
        local_scope = {
            "page": page, 
            "asyncio": asyncio,
            "expect": expect,
            "_memory": _browser_state["memory"], 
            "random": __import__("random"),
            "re": re
        }
        
        # We need to wrap the code in an async function to execute 'await'
        wrapped_code = f"async def _async_exec_wrapper():\n" + "\n".join([f"    {line}" for line in code.splitlines()]) + "\n"
        
        try:
            exec(wrapped_code, local_scope)
            await local_scope["_async_exec_wrapper"]()
            
            # Update global memory with any changes made by the AI
            _browser_state["memory"] = local_scope["_memory"]
            
            if _browser_state["memory"]:
                logger.info(f"Current Memory: {_browser_state['memory']}")
                
        finally:
            final_page_count = len(context.pages)
            if final_page_count > initial_page_count:
                new_page = context.pages[-1]
                logger.info(f"New Tab Detected! Switching control to: {new_page.url}")
                try:
                    await new_page.wait_for_load_state("domcontentloaded")
                    await new_page.bring_to_front()
                except Exception as e:
                    logger.warning(f"New page wait warning: {e}")
                
                _browser_state["page"] = new_page

    async def close_session(self):
        global _browser_state
        logger.info("Resetting Browser State...")
        try:
            if _browser_state["browser"]:
                await _browser_state["browser"].close()
            if _browser_state["playwright"]:
                await _browser_state["playwright"].stop()
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
        
        _browser_state["active"] = False
        _browser_state["page"] = None
        _browser_state["browser"] = None
        _browser_state["playwright"] = None
        _browser_state["memory"] = {}
