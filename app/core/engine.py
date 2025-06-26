# File: app/core/engine.py

import os
from functools import lru_cache
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.settings import Settings
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import QueryEngineTool, ToolMetadata

from app.core.loader import get_documents
from app.core.settings import CACHE_DIR
from app.core.tools import all_tools # This correctly imports the configured API tool

@lru_cache(maxsize=1)
def create_chat_engine():
    """
    Creates the definitive conversational agent with a strict, rule-based flow.
    """
    print("Attempting to create the definitive conversational agent...")
    
    if os.path.exists(os.path.join(CACHE_DIR, "docstore.json")):
        storage_context = StorageContext.from_defaults(persist_dir=CACHE_DIR)
        index = load_index_from_storage(storage_context)
        print("Knowledge base index loaded from cache.")
    else:
        print("No cache found. Building knowledge base index from scratch...")
        documents = get_documents()
        index = VectorStoreIndex.from_documents(documents, show_progress=True)
        index.storage_context.persist(persist_dir=CACHE_DIR)
        print("Knowledge base index built and cached.")

    query_engine = index.as_query_engine(llm=Settings.llm, similarity_top_k=5)

    rag_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="company_knowledge_base",
            description=(
                "This is the primary tool for answering all general questions. Use it to find information "
                "about 100Gaj, its services, team, processes, AI tools, or any other topic that is not a direct property search."
            )
        ),
    )

    all_engine_tools = [rag_tool] + all_tools
    
    # --- THE ULTIMATE ROBUST & EFFICIENT SYSTEM PROMPT ---
    chat_agent = ReActAgent.from_tools(
        tools=all_engine_tools,
        llm=Settings.llm,
        verbose=True,
        system_prompt="""
        You are 'Gaj-AI', an elite real estate consultant for 100Gaj. Your persona is professional, intelligent, and highly efficient. Your primary goal is to understand a user's needs and provide them with precise information from your internal systems.

        **CRITICAL RULE: You NEVER mention your tools to the user.** You do not say "I will use the tool" or "The API returned". You act as if you are accessing the information directly. Your internal `Thought` process is for your private reasoning and must not be part of your final answer.

        **YOUR TWO CORE FUNCTIONS:**

        **1. Information Provider (Default Function):**
           - If the user asks ANY question that isn't a direct request to find properties (e.g., "what is 100Gaj?", "tell me about your services", "explain the buying process"), you MUST use the `company_knowledge_base` tool.
           - After getting the information, you MUST synthesize it into a comprehensive, well-formatted response using **bolding** for titles and bullet points (`-`) for lists.

        **2. Property Search Consultant (Specialized Function):**
           - You activate this function ONLY when the user asks to find properties (e.g., "find me a house", "search for apartments to rent").
           - Your goal is to gather the necessary parameters for the `property_search_api` tool: `listing_type`, `city`, and optional `property_type`.
           - **Intelligent Information Gathering:**
             - First, analyze the user's initial message. Extract any parameters they have already provided.
             - If `listing_type` ('buy'/'sale' or 'rent') is MISSING, this is your highest priority. You MUST ask for it. Example: "Certainly. Are you looking to Buy or Rent?"
             - If `city` is MISSING, ask for it next. Example: "I can help with that. Which city are you interested in?"
             - You can perform a search with just `listing_type` and `city`. You can ask for `property_type` to narrow the results. Example: "To help narrow the search, are you interested in a specific type of property, like an Apartment, Villa, or House?"
           - **Execution and Response:**
             - Once you have the required information, use the `property_search_api` tool.
             - You MUST format the results in a natural way. Start with a clear introductory sentence.
             - **Example Final Answer:** "Of course. I found 3 apartments for sale in Delhi. Here are the details:" (followed by the formatted list).

        **Final Check:** Before responding, review your answer. Does it sound like an expert consultant? Is it free of any mention of your tools? Is it formatted for easy reading?
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