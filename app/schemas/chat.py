from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    """Defines the structure of a single message in the chat history."""
    role: str
    content: str

class ChatRequest(BaseModel):
    """Defines the structure of a request to the /chat endpoint."""
    message: str
    chat_history: Optional[List[ChatMessage]] = None