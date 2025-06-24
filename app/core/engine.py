import os
from functools import lru_cache
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core.settings import Settings
from llama_index.core.prompts import PromptTemplate

from app.core.loader import get_documents
from app.core.settings import CACHE_DIR

@lru_cache(maxsize=1)
def create_chat_engine():
    """
    Creates and returns a simple, strict, and efficient RAG query engine.
    """
    print("Attempting to create simple, strict RAG engine...")
    
    if os.path.exists(os.path.join(CACHE_DIR, "docstore.json")):
        print(f"Loading knowledge base from cache: {CACHE_DIR}")
        storage_context = StorageContext.from_defaults(persist_dir=CACHE_DIR)
        index = load_index_from_storage(storage_context)
    else:
        print("No cache found. Building knowledge base from documents...")
        documents = get_documents()
        index = VectorStoreIndex.from_documents(documents, show_progress=True)
        print(f"Persisting knowledge base to cache: {CACHE_DIR}")
        index.storage_context.persist(persist_dir=CACHE_DIR)

    query_engine = index.as_query_engine(
        streaming=True, 
        llm=Settings.llm,
        similarity_top_k=5,
    )
    
    qa_template_str = (
        "You are the 100Gaj AI Assistant, a professional and helpful AI for the 100Gaj real estate company.\n"
        "Your main purpose is to answer user questions about the company's services, properties, agents, and market insights based ONLY on the provided context.\n"
        "If the context does not contain the information to answer the question, you MUST respond with: "
        "'I can only answer questions related to 100Gaj. Please ask about our properties, services, or AI tools.'\n"
        "Do not use any external knowledge. Format lists using Markdown.\n"
        "---------------------\n"
        "Context: {context_str}\n"
        "---------------------\n"
        "Question: {query_str}\n"
        "Answer: "
    )
    
    query_engine.update_prompts(
        {"response_synthesizer:text_qa_template": PromptTemplate(qa_template_str)}
    )

    print("Simple, strict RAG engine created successfully.")
    return query_engine

def get_chat_engine():
    return create_chat_engine()

def clear_engine_cache():
    create_chat_engine.cache_clear()
    print("In-memory RAG engine cache cleared.")