from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """Defines the structure of a request to the /chat endpoint."""
    message: str = Field(..., description="The user's message to the chatbot")