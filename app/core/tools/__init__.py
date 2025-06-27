# File: app/core/tools/__init__.py

from .api_property_search import property_database_tool

# We now only have one tool for all property-related tasks.
all_tools = [
    property_database_tool,
]