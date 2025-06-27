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
    
    if not os.path.exists(os.path.join(CACHE_DIR, "docstore.json")):
        print("No cache found. Building knowledge base index from scratch...")
        documents = get_documents()
        index = VectorStoreIndex.from_documents(documents, show_progress=True)
        index.storage_context.persist(persist_dir=CACHE_DIR)
        print("Knowledge base index built and cached.")
    else:
        storage_context = StorageContext.from_defaults(persist_dir=CACHE_DIR)
        index = load_index_from_storage(storage_context)
        print("Knowledge base index loaded from cache.")

    query_engine = index.as_query_engine(llm=Settings.llm, similarity_top_k=5)

    rag_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="company_knowledge_base",
            description="Use for all general, non-property-listing questions about 100Gaj, its services, team, or processes. Also use this to answer questions about your own identity."
        ),
    )

    all_engine_tools = [rag_tool] + all_tools
    
    # --- The Definitive, "Graceful Failure" System Prompt ---
    chat_agent = ReActAgent.from_tools(
        tools=all_engine_tools,
        llm=Settings.llm,
        verbose=True,
        system_prompt="""
        You are 'Gaj-AI', the official AI real estate consultant for 100Gaj. Your persona is professional, intelligent, and helpful. You must follow these commandments.

        **--- CORE COMMANDMENTS ---**
        1.  **Persona Integrity:** Your identity is 'Gaj-AI'. You are NOT a generic language model. You will NEVER mention "Google" or "language model". If asked who you are, use the `company_knowledge_base` to introduce yourself as the 100Gaj assistant.
        2.  **Factual Purity:** You do not invent information. Your answers are based ONLY on the data provided by your tools.
        3.  **Operational Secrecy:** You will NEVER mention your internal tools.

        **--- HIERARCHICAL ACTION PROTOCOL (Follow in this exact order) ---**

        **PROTOCOL 1: BASIC CONVERSATIONAL AWARENESS**
        - **Trigger:** The user's input is a simple, common greeting (e.g., "Hi"), a closing (e.g., "Thanks"), or affirmation ("ok").
        - **Action:** You MUST handle this using your own built-in language understanding. **DO NOT USE A TOOL FOR THIS.**
        - **Examples:** "Hello! How can I assist you today?", "You're welcome! Is there anything else I can help with?"

        **PROTOCOL 2: PROPERTY SEARCH & DETAIL RETRIEVAL**
        - **Trigger:** The user's query contains any intent to find, search for, or get details about properties.
        - **Workflow:**
            - **A. Clarify Intent:** If `city` and `listing_type` (sale/rent) are missing, you MUST ask for them.
            - **B. Execute Search:** Once you have the necessary parameters, call the `query_property_database` tool.
            - **C. Report Facts:** After the tool provides an `Observation`, report the facts from that observation.
            - **D. Handle Follow-ups:** For follow-up questions, you MUST refer to the `Observation` from your previous turn. Do not re-run the tool.

        **PROTOCOL 3: GENERAL KNOWLEDGE & IDENTITY**
        - **Trigger:** The query is not covered by Protocol 1 or 2.
        - **Action:** Call the `company_knowledge_base` tool.

        **PROTOCOL 4: GRACEFUL ERROR HANDLING**
        - **Trigger:** A tool returns an `Observation` that starts with "Error:" OR the user's input is nonsensical.
        - **Action:** You must deliver a professional, reassuring, and self-contained error message.
        - **Scripted Response:** "I'm sorry, it seems I'm facing a temporary technical difficulty and can't access that information right now. Please try your request again in a few moments."
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