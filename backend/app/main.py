import sys
import os
print(f"SYS PATH: {sys.path}")
import app
print(f"APP MODULE: {app}")
print(f"APP FILE: {app.__file__}")
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints
import sys
import asyncio

# nest_asyncio is NOT needed for async_playwright and can cause conflicts
# import nest_asyncio
# nest_asyncio.apply()

# Fix for Playwright on Windows: Ensure ProactorEventLoop is used
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title="AI Test Case Generator API")

# Debug: Check Event Loop
try:
    loop = asyncio.get_running_loop()
    print(f"DEBUG: Current Event Loop: {loop}")
    if sys.platform == 'win32':
        print(f"DEBUG: Is Proactor? {isinstance(loop, asyncio.ProactorEventLoop)}")
except RuntimeError:
    print("DEBUG: No running event loop yet.")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    tb = traceback.format_exc()
    print(tb)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc), "traceback": tb},
    )

# Configure CORS to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(endpoints.router, prefix="/api/v1")

# Debug: Print all routes
for route in app.routes:
    print(f"DEBUG Route: {route.path} {route.name}")

@app.get("/")
def read_root():
    return {"message": "AI Test Case Generator API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
