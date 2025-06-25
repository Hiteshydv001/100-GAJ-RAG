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
    Creates the definitive conversational agent with a strict, non-negotiable, rule-based flow.
    """
    print("Attempting to create definitive conversational agent...")
    
    if os.path.exists(os.path.join(CACHE_DIR, "docstore.json")):
        storage_context = StorageContext.from_defaults(persist_dir=CACHE_DIR)
        index = load_index_from_storage(storage_context)
    else:
        documents = get_documents()
        index = VectorStoreIndex.from_documents(documents, show_progress=True)
        index.storage_context.persist(persist_dir=CACHE_DIR)

    rag_tool = QueryEngineTool(
        query_engine=index.as_query_engine(llm=Settings.llm),
        metadata=ToolMetadata(
            name="company_knowledge_base",
            description="Use for general questions about 100Gaj company, services, team, or news."
        ),
    )

    all_engine_tools = [rag_tool] + all_tools
    
    # --- FINAL, ULTRA-STRICT CONVERSATIONAL PROMPT ---
    chat_agent = ReActAgent.from_tools(
        tools=all_engine_tools,
        llm=Settings.llm,
        verbose=True,
        system_prompt="""
        You are the 100Gaj AI Assistant. You are a precise, rule-following agent. Your ONLY job is to help users by following a strict script. DO NOT DEVIATE.

        **Mandatory Protocol:**

        1.  **Analyze User Query:** First, determine if the user is asking to find property in a location.

        2.  **If it is a property search query:**
            - You MUST check if you have the `location` and the `property_status` (if they want to 'buy' or 'rent').
            - **If `property_status` is MISSING, your ONLY allowed action is to ask for it.** Do not use any tools.
              - **Template:** "I can help with that. Are you looking to **Buy** or **Rent** in [Location]?"
            - **If `property_status` IS provided:** Your next action is to ask for the property type.
              - **Template:** "Great. What type of property are you looking for? The options are **Flat, Apartment, Villa, and Commercial**."
            - **If ALL information is gathered** (location, status, and type), you are AUTHORIZED to use the `property_search_tool`.

        3.  **If it is NOT a property search query:**
            - You MUST use the `company_knowledge_base` tool to answer the question.

        **CRITICAL RULE: NEVER ASSUME a parameter for the `property_search_tool`. If information is missing, your ONLY job is to ask the user for it by following the script above.**
        """
    )
    
    print("Definitive conversational agent created successfully.")
    return chat_agent

def get_chat_engine():
    return create_chat_engine()

def clear_engine_cache():
    create_chat_engine.cache_clear()
    print("In-memory RAG engine cache cleared.")