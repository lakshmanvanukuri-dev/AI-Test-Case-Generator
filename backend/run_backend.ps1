$env:PYTHONPATH = "C:\Users\Lakshman Kumar V\Desktop\AI Test Case Generator\ai-test-case-generator\backend"
& "C:\Users\Lakshman Kumar V\Desktop\AI Test Case Generator\.venv\Scripts\Activate.ps1"
python -m uvicorn app.main:app --reload --port 8004 --env-file "C:\Users\Lakshman Kumar V\Desktop\AI Test Case Generator\ai-test-case-generator\backend\.env"
Read-Host "Press Enter to exit..."