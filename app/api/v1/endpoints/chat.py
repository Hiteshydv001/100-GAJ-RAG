# File: app/api/v1/endpoints/chat.py

import json
import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from llama_index.core.agent import ReActAgent
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, GoogleAPICallError
from typing import Optional

from app.core.engine import get_chat_engine
from app.schemas.chat import ChatRequest

router = APIRouter()
logger = logging.getLogger(__name__)

async def retry_with_exponential_backoff(func, max_retries: int = 3, initial_delay: float = 1.0):
    """Retries a function with exponential backoff."""
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await func()
        except (ResourceExhausted, ServiceUnavailable) as e:
            last_exception = e
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= 2
            continue
        except Exception as e:
            raise e
    
    raise last_exception

@router.post("")
async def chat(
    request: ChatRequest,
    agent: ReActAgent = Depends(get_chat_engine)
):
    """
    Chat endpoint that processes user queries and returns responses.
    Includes retry logic for handling API rate limits.
    """
    async def generate():
        try:
            # Wrap the agent.achat call in retry logic
            async def attempt_chat():
                return await agent.achat(request.message)
            
            response = await retry_with_exponential_backoff(
                lambda: attempt_chat(),
                max_retries=3,
                initial_delay=1.0
            )
            
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
            logger.warning(f"Resource exhausted after retries: {str(e)}")
            error_msg = json.dumps({
                "type": "text",
                "data": "Hello! I'm currently experiencing high demand. Let me help you with your query about properties. What type of property are you looking for?"
            })
            yield f"data: {error_msg}\n\n"
        except ServiceUnavailable as e:
            logger.warning(f"Service unavailable after retries: {str(e)}")
            error_msg = json.dumps({
                "type": "text",
                "data": "I'm here to help! While our systems are adjusting, could you tell me what kind of property you're interested in?"
            })
            yield f"data: {error_msg}\n\n"
        except GoogleAPICallError as e:
            logger.error(f"Google API error: {str(e)}")
            error_msg = json.dumps({
                "type": "text",
                "data": "I'm ready to assist you with finding properties. What are you looking for today?"
            })
            yield f"data: {error_msg}\n\n"
        except Exception as e:
            logger.error(f"Unexpected error in chat endpoint: {str(e)}", exc_info=True)
            error_msg = json.dumps({
                "type": "text",
                "data": "I'm here to help you find the perfect property. What features are you looking for?"
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