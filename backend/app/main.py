"""
FastAPI application entry point for Simple FRED Site backend.
"""

import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
# Look for .env in the project root (parent of backend directory)
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"Loaded .env file from: {env_path}")
else:
    # Fallback: try loading from current directory
    load_dotenv()
    logger.warning("Using fallback .env loading from current directory")

app = FastAPI(
    title="Simple FRED Site API",
    description="API for fetching FRED economic data, browsing by categories, and generating AI summaries",
    version="1.0.0",
)


# Add request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all incoming requests."""
    import time

    start_time = time.time()

    logger.info(f"Incoming request: {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        elapsed = time.time() - start_time
        logger.info(f"Response: {response.status_code} | Time: {elapsed:.3f}s")
        return response
    except Exception as e:
        logger.error(f"Error in request: {str(e)}", exc_info=True)
        raise


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(routes.router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    logger.info("Health check endpoint called")
    return {"status": "healthy", "service": "Simple FRED Site API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
