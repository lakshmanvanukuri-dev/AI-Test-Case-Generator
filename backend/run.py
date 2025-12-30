import sys
import asyncio
import uvicorn

if __name__ == "__main__":
    # Force ProactorEventLoop on Windows for Playwright
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    print("Starting Uvicorn with ProactorEventLoop...")
    # Run Uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8008, reload=False)
    
    # Alternative: Run programmatically
    # config = uvicorn.Config("app.main:app", host="0.0.0.0", port=8003, reload=False)
    # server = uvicorn.Server(config)
    # server.run()
