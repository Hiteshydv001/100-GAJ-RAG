# File: app/api/v1/endpoints/chat.py

import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from llama_index.core.agent import ReActAgent
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, GoogleAPICallError

from app.core.engine import get_chat_engine
from app.schemas.chat import ChatRequest

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("")
async def chat(
    request: ChatRequest,
    agent: ReActAgent = Depends(get_chat_engine)
):
    """
    Chat endpoint that processes user queries and returns responses.
    """
    async def generate():
        try:
            response = await agent.achat(request.message)
            
            if not response or not hasattr(response, 'response'):
                error_msg = json.dumps({
                    "type": "text",
                    "data": "I apologize, but I've encountered an error processing your request. Please try again."
                })
                yield f"data: {error_msg}\n\n"
                return

            # Send the response text
            message = json.dumps({
                "type": "text",
                "data": response.response
            })
            yield f"data: {message}\n\n"

            # Send end marker
            yield f"data: {json.dumps({'type': 'end'})}\n\n"

        except ResourceExhausted as e:
            error_msg = json.dumps({
                "type": "text",
                "data": "The AI service is currently at its usage limit. Please try again later."
            })
            yield f"data: {error_msg}\n\n"
        except ServiceUnavailable as e:
            error_msg = json.dumps({
                "type": "text",
                "data": "The service is temporarily unavailable. Please try again shortly."
            })
            yield f"data: {error_msg}\n\n"
        except GoogleAPICallError as e:
            error_msg = json.dumps({
                "type": "text",
                "data": f"An error occurred while processing your request: {str(e)}"
            })
            yield f"data: {error_msg}\n\n"
        except Exception as e:
            logger.error(f"Unexpected error in chat endpoint: {str(e)}", exc_info=True)
            error_msg = json.dumps({
                "type": "text",
                "data": "An unexpected error occurred. Please try again."
            })
            yield f"data: {error_msg}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )