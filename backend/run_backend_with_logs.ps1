$env:PYTHONPATH = "C:\Users\Lakshman Kumar V\Desktop\AI Test Case Generator\ai-test-case-generator\backend"
& "C:\Users\Lakshman Kumar V\Desktop\AI Test Case Generator\.venv\Scripts\Activate.ps1"
cd "C:\Users\Lakshman Kumar V\Desktop\AI Test Case Generator\ai-test-case-generator\backend"
python -m uvicorn app.main:app --reload --port 8004 --env-file .env > backend.log 2>&1