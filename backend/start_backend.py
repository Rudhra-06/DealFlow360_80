import uvicorn
import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    print("Starting DealFlow360 FastAPI Backend Server on http://127.0.0.1:8000...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
