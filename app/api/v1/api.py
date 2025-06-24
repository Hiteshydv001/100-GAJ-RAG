from fastapi import APIRouter
from .endpoints import chat

# The 'upload' router has been removed.
api_router = APIRouter()
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])