from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router as api_router
from app.models.responses import ErrorResponse
import uvicorn
import sys
import os
from datetime import datetime
import uuid

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create FastAPI app
app = FastAPI(
    title="Medical Clinic AI Agent",
    description="AI system for medical clinic to assist doctors and patients",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API routes
app.include_router(api_router, prefix="/api/ai")

# Root endpoint - redirect to docs
@app.get("/")
async def root():
    return {"message": "Welcome to the Medical Clinic AI API. Visit /docs for API documentation."}

# Global exception handler to format errors like the backend API
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error_response = {
        "error": {
            "code": exc.status_code,
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": str(uuid.uuid4())
        }
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=exc.headers,
    )

# General exception handler for unexpected errors
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    error_response = {
        "error": {
            "code": 500,
            "message": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": str(uuid.uuid4())
        }
    }
    return JSONResponse(
        status_code=500,
        content=error_response,
    )

if __name__ == "__main__":
    # Check if port is provided as an environment variable
    port = int(os.getenv("PORT", 8081))
    
    print(f"Starting Medical Clinic AI Agent on port {port}...")
    print(f"Documentation available at http://localhost:{port}/docs")
    
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)