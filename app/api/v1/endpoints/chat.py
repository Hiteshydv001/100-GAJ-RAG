import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from llama_index.core.query_engine import BaseQueryEngine
from llama_index.core.base.response.schema import StreamingResponse as LlamaStreamingResponse

from app.core.engine import get_chat_engine
from app.schemas.chat import ChatRequest

router = APIRouter()

GREETINGS = {"hello", "hi", "hey", "yo", "greetings", "good morning", "good afternoon", "good evening"}
SUMMARY_KEYWORDS = {"company summary", "company overview", "tell me about 100gaj", "who are you"}

@router.post("")
async def chat(
    request: ChatRequest,
    query_engine: BaseQueryEngine = Depends(get_chat_engine)
):
    user_message = request.message.strip()
    user_message_lower = user_message.lower()
    final_query = user_message

    if user_message_lower in GREETINGS:
        async def greeting_generator():
            canned_response = "Hello! I am the 100Gaj AI Assistant. How can I help you with questions about our properties, services, or the real estate market?"
            yield f"data: {json.dumps({'type': 'text', 'data': canned_response})}\n\n"
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
        return StreamingResponse(greeting_generator(), media_type="text/event-stream")

    elif any(keyword in user_message_lower for keyword in SUMMARY_KEYWORDS):
        print("Summary intent detected. Transforming query.")
        final_query = (
            "Generate a comprehensive summary of the 100Gaj company. "
            "Include these sections: "
            "1. A professional summary statement. "
            "2. The company's mission and vision. "
            "3. An overview of key services and AI tools offered. "
            "4. A list of top agents and premium builders they partner with. "
            "Synthesize this from all available context."
        )
    
    elif request.chat_history:
        history_str = "\n".join(
            f"{msg.role}: {msg.content}" 
            for msg in request.chat_history 
            if msg.content and msg.content.strip()
        )
        final_query = f"Conversation History:\n{history_str}\n\nUser's Current Question: {user_message}"

    response_stream = query_engine.query(final_query)

    async def event_generator():
        if isinstance(response_stream, LlamaStreamingResponse):
            for token in response_stream.response_gen:
                yield f"data: {json.dumps({'type': 'text', 'data': token})}\n\n"
            
            source_nodes = [
                {"id": node.node.id_, "text": node.node.get_content()[:1000] + "...", "score": node.score}
                for node in response_stream.source_nodes
            ]
            if source_nodes:
                yield f"data: {json.dumps({'type': 'sources', 'data': source_nodes})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'text', 'data': str(response_stream)})}\n\n"

        yield f"data: {json.dumps({'type': 'end'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")