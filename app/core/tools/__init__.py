# File: app/core/tools/__init__.py

from .api_property_search import api_property_search_tool, get_property_details_tool

# List all available tools for the agent
all_tools = [
    api_property_search_tool,
    get_property_details_tool,
]