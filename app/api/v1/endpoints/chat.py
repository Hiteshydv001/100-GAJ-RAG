# File: app/api/v1/endpoints/chat.py

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from llama_index.core.agent import ReActAgent
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.base.llms.types import ChatMessage as LlamaChatMessage
# Add the specific error for rate limiting
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, GoogleAPICallError

from app.core.engine import get_chat_engine
from app.schemas.chat import ChatRequest

router = APIRouter()

@router.post("")
async def chat(
    request: ChatRequest,
    agent: ReActAgent = Depends(get_chat_engine)
):
    chat_history = []
    if request.chat_history:
        chat_history = [
            LlamaChatMessage(role=msg.role, content=msg.content)
            for msg in request.chat_history if msg.content and msg.content.strip()
        ]
    
    try:
        response_stream = await agent.astream_chat(
            request.message, chat_history=chat_history
        )

    # --- ROBUST ERROR HANDLING FOR GOOGLE API ---
    except ResourceExhausted:
        # This catches the "API limit reached" error
        raise HTTPException(
            status_code=429, # "Too Many Requests" is the standard HTTP code for this
            detail="The AI service is currently at its usage limit. Please try again later."
        )
    except ServiceUnavailable:
        raise HTTPException(
            status_code=503,
            detail="The AI model is currently overloaded. Please try your request again in a moment."
        )
    except GoogleAPICallError as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred with the AI service: {e}"
        )
    # --- END OF ERROR HANDLING ---

    async def event_generator():
        try:
            async for token in response_stream.async_response_gen():
                yield f"data: {json.dumps({'type': 'text', 'data': token})}\n\n"
            
            if isinstance(response_stream, AgentChatResponse):
                source_nodes = [
                    {"id": node.node.id_, "text": node.node.get_content()[:1000] + "...", "score": node.score}
                    for node in response_stream.source_nodes
                ]
                if source_nodes:
                    yield f"data: {json.dumps({'type': 'sources', 'data': source_nodes})}\n\n"

            yield f"data: {json.dumps({'type': 'end'})}\n\n"
        
        except (ResourceExhausted, ServiceUnavailable):
            error_message = "I'm sorry, the connection to the AI service was interrupted due to high demand. Please try sending your message again."
            yield f"data: {json.dumps({'type': 'text', 'data': error_message})}\n\n"
            yield f"data: {json.dumps({'type': 'end'})}\n\n"


    return StreamingResponse(event_generator(), media_type="text/event-stream")