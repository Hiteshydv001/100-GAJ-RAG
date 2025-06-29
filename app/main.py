# File: app/main.py

from fastapi import FastAPI, Response, status # <-- Add Response and status
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.settings import settings  # Import the initialized settings
from app.core.engine import get_chat_engine
import logging # <-- Let's use the logging we discussed

# Configure logging - only show INFO and above
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

app = FastAPI(
    title="100Gaj AI Assistant API",
    version="1.0.0",
)

# Configure CORS to allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- ADD THIS NEW ENDPOINT ---
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    Handles the browser's request for a favicon.
    Returns a 204 No Content response to prevent 404 errors in the log.
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)
# -----------------------------


# Include the API router
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize settings and resources on startup."""
    # Pre-build the engine to avoid cold starts on first request
    get_chat_engine()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    pass

@app.get("/", tags=["Health Check"])
def health_check():
    """A simple health check endpoint to confirm the server is running."""
    return {"status": "ok", "message": "100Gaj API is running"}