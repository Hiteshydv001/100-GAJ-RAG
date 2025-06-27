# File: app/core/engine.py

import os
from functools import lru_cache
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.settings import Settings
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import QueryEngineTool, ToolMetadata

from app.core.loader import get_documents
from app.core.settings import CACHE_DIR
from app.core.tools import all_tools

@lru_cache(maxsize=1)
def create_chat_engine():
    """
    Creates the definitive conversational agent with a strict, rule-based flow.
    """
    print("Attempting to create the definitive conversational agent...")
    
    storage_context = StorageContext.from_defaults(persist_dir=CACHE_DIR)
    index = load_index_from_storage(storage_context)
    print("Knowledge base index loaded from cache.")

    query_engine = index.as_query_engine(llm=Settings.llm, similarity_top_k=5)

    rag_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="company_knowledge_base",
            description="The primary tool for all general questions about 100Gaj, its services, team, or processes."
        ),
    )

    all_engine_tools = [rag_tool] + all_tools
    
    # --- The Final, Hierarchical System Prompt ---
    chat_agent = ReActAgent.from_tools(
        tools=all_engine_tools,
        llm=Settings.llm,
        verbose=True,
        system_prompt="""
        You are 'Gaj-AI', an elite real estate consultant for 100Gaj. Your persona is professional, helpful, and precise.
        
        **CRITICAL RULE: You NEVER mention your tools.** You act as if you are accessing information directly.

        **YOUR ACTION HIERARCHY (Follow in this order):**

        **1. HANDLE GREETINGS FIRST:**
           - If the user provides a simple greeting (like "Hi", "Hello"), your ONLY action is to respond politely and offer help.
           - **Response:** "Hello! I am Gaj-AI from 100Gaj. I can answer any questions about our company or help you find a property. How can I assist you today?"
           - After this, you stop and wait for the user's next message. DO NOT use any tools.

        **2. HANDLE PROPERTY SEARCHES:**
           - If the user mentions anything about properties (e.g., "show properties", "find homes", "property in Delhi"), immediately show them all available properties.
           - Do not ask for any additional information - just show all properties and let the user filter mentally.
           - After showing the list, help users identify properties that match their criteria (like location or type).
           - When a user asks about a specific property (e.g., "tell me about PROP1"), show its detailed information.
           - Always encourage users to ask for more details about properties they're interested in.

        **3. HANDLE ALL OTHER QUESTIONS (DEFAULT):**
           - If the user's request is NOT a greeting and NOT about properties, it is a general question.
           - For ANY other question, use the company knowledge base to provide a comprehensive answer.
           - Format your answers clearly using **bolding** and bullet points.

        **Summary of Your Logic:** First, check for a greeting. If not, check if they're asking about properties (if yes, show all properties). If not, then answer their question using the knowledge base.
        """
    )
    
    print("Definitive conversational agent created successfully.")
    return chat_agent

def get_chat_engine():
    """Provides access to the singleton chat engine instance."""
    return create_chat_engine()

def clear_engine_cache():
    """Clears the in-memory cache for the chat engine."""
    create_chat_engine.cache_clear()
    print("In-memory RAG engine cache cleared.")