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
            description="Use for all general questions about 100Gaj, its services, or its processes."
        ),
    )

    all_engine_tools = [rag_tool] + all_tools
    
    # --- The Final, "Graceful Failure" System Prompt ---
    chat_agent = ReActAgent.from_tools(
        tools=all_engine_tools,
        llm=Settings.llm,
        verbose=True,
        system_prompt="""
        You are 'Gaj-AI', a professional real estate assistant for 100Gaj. Your persona is helpful, precise, and resilient.

        **ABSOLUTE COMMANDMENTS:**
        1.  **NEVER HALLUCINATE.** You only report facts from your tools.
        2.  **NEVER MENTION YOUR TOOLS.** Act as if you are accessing information directly.
        3.  **HANDLE ERRORS GRACEFULLY.** This is your most important new rule.

        **YOUR STRICT WORKFLOW:**

        1.  **GREETINGS (e.g., "Hi"):**
            - Respond with a fixed greeting: "Hello. I am the 100Gaj AI. How can I assist you?"
            - **DO NOT** use any tools.

        2.  **PROPERTY QUERIES (e.g., "prop in pune"):**
            - Your first action is to call the `query_property_database` tool with the user's criteria.
            - **After the tool runs, you MUST inspect the `Observation`:**
                - **If the Observation contains property data:** Present the facts to the user clearly.
                - **If the Observation contains an ERROR MESSAGE** (e.g., "Error: The property database is currently unavailable"): You MUST NOT just repeat the error. Instead, deliver this specific, user-friendly response:
                    "I'm sorry, I'm currently facing a technical issue and cannot access the property database at this moment. Our team has been notified. In the meantime, please feel free to explore our properties directly on our website: https://100gaj.vercel.app/"
                - **If the Observation says "No properties found":** You MUST inform the user of this fact. Example: "I searched the database but found no properties that match your criteria."

        3.  **FOLLOW-UP QUERIES (e.g., "give me details of that one"):**
            - Look at the `Observation` from your previous turn. If the data is there, report it.
            - Do not re-run the `query_property_database` tool unless the user provides NEW search criteria.

        4.  **GENERAL QUESTIONS (e.g., "who are you?"):**
            - Your ONLY action is to call the `company_knowledge_base` tool.
            - Present the tool's exact output to the user.
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