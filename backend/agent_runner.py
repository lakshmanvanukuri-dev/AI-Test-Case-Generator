import sys
import json
import os
import re
import time
import traceback
import google.generativeai as genai
from playwright.sync_api import sync_playwright, Page, expect

# Load environment variables manually since we are in a subprocess
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print(json.dumps({"error": "GOOGLE_API_KEY not found in environment"}))
    sys.exit(1)

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-pro')

def run_agent(test_steps, user_context):
    results = []
    recorded_code = []
    
    try:
        with sync_playwright() as p:
            # --- LAUNCH BROWSER ---
            try:
                browser = p.chromium.launch(headless=False, slow_mo=1000, args=["--start-maximized"])
                context = browser.new_context(viewport=None)
            except Exception:
                # Fallback
                browser = p.chromium.launch(headless=False, slow_mo=1000)
                context = browser.new_context()
            
            page = context.new_page()
            
            # --- NAVIGATE ---
            # Extract URL
            url_match = re.search(r'https?://[^\s]+', user_context)
            if url_match:
                target_url = url_match.group(0)
                try:
                    page.goto(target_url, timeout=60000)
                    page.wait_for_load_state("domcontentloaded")
                    results.append({"step": "Navigate", "status": "Success", "detail": f"Opened {target_url}"})
                    recorded_code.append(f"page.goto('{target_url}')")
                except Exception as e:
                    results.append({"step": "Navigate", "status": "Failed", "detail": str(e)})
                    return results
            else:
                results.append({"step": "Setup", "status": "Failed", "detail": "No URL found"})
                return results

            # --- EXECUTE STEPS ---
            for step in test_steps:
                result = execute_step(page, step, user_context)
                results.append(result)
                if result["status"] == "Success":
                    recorded_code.append(result.get("code", ""))
                else:
                    break
            
            browser.close()

    except Exception as e:
        results.append({"step": "Critical Error", "status": "Failed", "detail": str(e)})
        traceback.print_exc()

    # --- GENERATE FINAL SCRIPT ---
    final_script = "import pytest\nfrom playwright.sync_api import Page, expect\n\ndef test_generated_scenario(page: Page):\n"
    for line in recorded_code:
        final_script += f"    {line}\n"
    
    results.append({
        "step": "Final Verified Code",
        "status": "Success",
        "detail": "Script generated.",
        "code_block": final_script
    })

    return results

def execute_step(page, step_description, user_context):
    # 1. Popup Killer
    try:
        page.keyboard.press("Escape")
        page.evaluate("""() => {
            const buttons = Array.from(document.querySelectorAll('button, [role="button"]'));
            const closeBtn = buttons.find(el => {
                const text = el.innerText ? el.innerText.trim().toLowerCase() : '';
                return ['✕', 'x', 'close', 'no thanks'].includes(text) && el.offsetParent !== null;
            });
            if (closeBtn) closeBtn.click();
        }""")
    except: pass

    # 2. Accessibility Tree
    try:
        tree_snapshot = page.evaluate("""() => {
            function isVisible(el) { return el.offsetParent !== null && el.style.display !== 'none'; }
            const els = Array.from(document.querySelectorAll('button, a, input, select, textarea, [role="button"]'));
            return els.filter(isVisible).map((el, i) => {
                const label = el.innerText || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '';
                const tag = el.tagName.toLowerCase();
                return `[ai-node-${i}] <${tag}> "${label.slice(0,50)}"`;
            }).join('\\n');
        }""")
    except: tree_snapshot = "DOM Unavailable"

    # 3. AI Decision
    try:
        prompt = f"""
        GOAL: {step_description}
        UI STATE:
        {tree_snapshot[:5000]}
        
        INSTRUCTIONS:
        1. Find the element in UI STATE matching the GOAL.
        2. Write Python Playwright (SYNC) code.
        3. Use `page.locator(...)` or `page.get_by_text(...)`.
        
        Return ONLY the Python code.
        """
        response = model.generate_content(prompt)
        code = response.text.strip().replace("```python", "").replace("```", "").strip()
        
        # Execute
        local_scope = {'page': page, 'expect': expect, 'time': time}
        exec(code, globals(), local_scope)
        return {"step": step_description, "status": "Success", "code": code}
        
    except Exception as e:
        return {"step": step_description, "status": "Failed", "detail": str(e)}

if __name__ == "__main__":
    # Read input from stdin
    try:
        input_data = sys.stdin.read()
        if not input_data:
            print(json.dumps({"error": "No input data provided"}))
            sys.exit(1)
            
        data = json.loads(input_data)
        steps = data.get("steps", [])
        context = data.get("context", "")
        
        results = run_agent(steps, context)
        
        # Print results as JSON to stdout
        print(json.dumps(results))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
