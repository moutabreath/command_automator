"""
FastAPI application for Commands Automator
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .utils.logger_config import setup_logging

# Import routers
from .jobs_tracking.api.job_tracking_router import router as job_tracking_router
from .llm_api.llm_router import router as llm_router
from .user.user_router import router as user_router

# Configure logging
setup_logging()

# Create FastAPI application
app = FastAPI(
    title="Job Seeker Automator API",
    description="API for automating job tracking, LLM operations, and user management",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for your use case
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(job_tracking_router)
app.include_router(llm_router)
app.include_router(user_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Commands Automator API",
        "docs": "/docs",
        "openapi_schema": "/openapi.json"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
