# File: app/core/tools/__init__.py

# from .live_property_scraper import live_property_search_tool # --- OLD
from .api_property_search import api_property_search_tool # +++ NEW

# List all available tools for the agent
all_tools = [
    api_property_search_tool,
]