# File: app/core/tools/api_property_search.py

import httpx
from llama_index.core.tools import FunctionTool
from typing import Optional, List, Dict, Union
import certifi
from functools import lru_cache

API_URL = "https://100gaj.vercel.app/api/properties"
_property_data_cache: List[Dict] = []

@lru_cache(maxsize=1)
def _fetch_all_data() -> List[Dict]:
    """Internal function to fetch and cache data from the API for the session."""
    global _property_data_cache
    if _property_data_cache:
        return _property_data_cache
    
    print(f"--- Fetching ALL properties from {API_URL} (This should happen only once per session) ---")
    try:
        ssl_context = httpx.create_ssl_context(verify=certifi.where())
        with httpx.Client(verify=ssl_context) as client:
            response = client.get(API_URL, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        
        if data.get("success") and data.get("properties"):
            _property_data_cache = data["properties"]
            return _property_data_cache
        return []
    except Exception as e:
        print(f"FATAL ERROR fetching property data: {e}")
        return []

def query_property_database(
    city: Optional[str] = None,
    listing_type: Optional[Union[str, List[str]]] = None,
    property_type: Optional[str] = None
) -> str:
    """
    Searches the in-memory property database based on provided filters.
    It can now handle a list of listing_types (e.g., ['sale', 'rent']).
    """
    all_properties = _fetch_all_data()
    if not all_properties:
        return "Error: The property database is currently unavailable or empty."

    results = all_properties

    if city:
        results = [p for p in results if p.get("address", {}).get("city", "").lower() == city.lower()]
    
    # --- BUG FIX: Handle both string and list for listing_type ---
    if listing_type:
        if isinstance(listing_type, str):
            listing_type_filters = [listing_type.lower().replace("buy", "sale")]
        else: # It's a list
            listing_type_filters = [lt.lower().replace("buy", "sale") for lt in listing_type]
        
        results = [p for p in results if p.get("listingType", "").lower() in listing_type_filters]
    # --- END OF BUG FIX ---

    if property_type:
        results = [p for p in results if p.get("propertyType", "").lower() == property_type.lower()]
    
    if not results:
        return "No properties in the database match your specified criteria."

    formatted_results = []
    for prop in results:
        address = prop.get("address", {})
        owner = prop.get("ownerDetails", {})
        price = prop.get("price", "N/A")
        price_str = f"₹{price:,}" if isinstance(price, (int, float)) else str(price)

        details = [
            f"--- Property Found ---",
            f"Title: {prop.get('title', 'N/A')}",
            f"Location: {address.get('city', 'N/A')} ({address.get('street', 'N/A')})",
            f"Listing: For {prop.get('listingType', 'N/A')} at {price_str}",
            f"Type: {prop.get('propertyType', 'N/A').capitalize()} with {prop.get('bedrooms', 'N/A')} bedrooms",
            f"Description: {prop.get('description', 'N/A').strip()}",
            f"Contact: {owner.get('name', 'N/A')} at {owner.get('phone', 'N/A')}",
            f"--- End of Property ---"
        ]
        formatted_results.append("\n".join(details))
    
    return "\n\n".join(formatted_results)

property_database_tool = FunctionTool.from_defaults(
    fn=query_property_database,
    name="query_property_database",
    description="Use this to find and list properties. You can filter by `city`, `listing_type` (sale/rent), and `property_type`."
)