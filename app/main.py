from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.settings import settings

app = FastAPI(
    title="100Gaj AI Assistant API",
    version="1.0.0",
)

# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
def on_startup():
    """Actions to perform on application startup."""
    print("--- Application starting up ---")
    from app.core.engine import get_chat_engine
    get_chat_engine()  # Pre-builds the engine to avoid cold starts on first request
    print("--- Application startup complete ---")

@app.get("/", tags=["Health Check"])
def health_check():
    """A simple health check endpoint to confirm the server is running."""
    return {"status": "ok", "message": "100Gaj API is running"}