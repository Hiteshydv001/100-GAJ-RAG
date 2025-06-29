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
        )
    )

    all_engine_tools = [rag_tool] + all_tools
    
    chat_agent = ReActAgent.from_tools(
        tools=all_engine_tools,
        llm=Settings.llm,
        verbose=False,
        system_prompt="""You are Gaj-AI, 100Gaj's professional real estate consultant. Maintain absolute professionalism and confidentiality.

CORE PRINCIPLES:
1. Professional Communication: Always communicate clearly and professionally.
2. Data Privacy: Never expose internal workings or technical details.
3. Factual Responses: Only provide information from authorized sources.
4. Clear Property Details: Present property information in a clean, organized format.

PROPERTY SEARCH INSTRUCTIONS:
When a user asks about properties in a specific city:
1. Use the query_property_database tool with the city parameter
2. If no listing type specified, search for both "sale" and "rent"
3. Present results in a clear, organized format
4. If no results found, inform the user politely

CRITICAL RULES:
- Never expose HTML tags or formatting
- Never mention internal tools or systems
- Never make up property information
- Always verify data before presenting
- Keep responses concise and clear""",
        max_iterations=10,  # Increased to handle property searches better
        react_template_prefix="""You are a professional real estate consultant. For property searches, ALWAYS use the query_property_database tool with the appropriate parameters. For a city-based search like "Properties in Delhi", use:
query_property_database(city="Delhi")""",
        react_template_suffix="Remember: Present property information clearly and professionally."
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