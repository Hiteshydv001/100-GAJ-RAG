import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from llama_index.core.agent import ReActAgent
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.base.llms.types import ChatMessage as LlamaChatMessage

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
    
    response_stream = await agent.astream_chat(
        request.message, chat_history=chat_history
    )

    async def event_generator():
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

    return StreamingResponse(event_generator(), media_type="text/event-stream")