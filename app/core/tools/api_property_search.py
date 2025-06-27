# File: app/core/tools/api_property_search.py

import httpx
from llama_index.core.tools import FunctionTool
from typing import Optional, Dict
import certifi

API_URL = "https://100gaj.vercel.app/api/properties"
property_search_cache: Dict[str, Dict] = {}

def search_properties_via_api(listing_type: str, city: str, property_type: Optional[str] = None) -> str:
    """
    Searches for properties via the API, filters them client-side for accuracy, and returns a clear, summarized list.
    """
    global property_search_cache
    property_search_cache.clear()

    print(f"--- Executing API Search: type={listing_type}, property={property_type}, city={city} ---")
    
    listing_type_api = 'sale' if listing_type.lower() == 'buy' else listing_type.lower()
    params = {"listingType": listing_type_api}
    
    try:
        ssl_context = httpx.create_ssl_context(verify=certifi.where())
        with httpx.Client(verify=ssl_context) as client:
            response = client.get(API_URL, params=params, timeout=20.0)
            response.raise_for_status()
            data = response.json()

        if not data.get("success") or not data.get("properties"):
            return f"The API did not return any properties for the '{listing_type}' category."

        all_properties = data["properties"]
        
        # --- CRITICAL FIX: ACCURATE FILTERING ---
        filtered_properties = [
            prop for prop in all_properties 
            if prop.get("address", {}).get("city", "").lower() == city.lower() and
            (not property_type or prop.get("propertyType", "").lower() == property_type.lower())
        ]
        # --- END OF FIX ---

        if not filtered_properties:
            search_summary = f"for {listing_type} in {city}"
            if property_type:
                search_summary += f" of type '{property_type}'"
            return f"I searched the database but found no properties matching your criteria ({search_summary})."

        formatted_results = []
        for i, prop in enumerate(filtered_properties):
            prop_id = f"PROP{i+1}"
            property_search_cache[prop_id] = prop

            price = prop.get("price", "N/A")
            price_str = f"₹{price:,}" if isinstance(price, (int, float)) else str(price)

            details = (
                f"**[{prop_id}] {prop.get('title', 'N/A')}**\n"
                f"   - Type: {prop.get('propertyType', 'N/A').capitalize()} ({prop.get('bedrooms', 'N/A')} Bed)\n"
                f"   - Price: {price_str}"
            )
            formatted_results.append(details)
        
        # This response confirms EXACTLY what was searched for.
        confirmation_msg = f"I found {len(filtered_properties)} properties for {listing_type} in {city}"
        if property_type:
            confirmation_msg += f" of type '{property_type}'"
        
        return f"{confirmation_msg}. Here are the summaries:\n\n" + "\n\n".join(formatted_results)

    except Exception as e:
        return f"An unexpected error occurred while searching for properties: {str(e)}"

def get_property_details(property_id: str) -> str:
    """
    Retrieves the full, detailed information for a single property from the last search results.
    """
    if not property_search_cache:
        return "You must perform a search first before asking for details. I don't have any properties in memory."

    prop = property_search_cache.get(property_id.upper())
    if not prop:
        return f"Invalid ID '{property_id}'. Please provide one of the IDs from the recent search results (e.g., PROP1)."

    price = prop.get("price", "N/A")
    price_str = f"₹{price:,}" if isinstance(price, (int, float)) else str(price)
    address = prop.get("address", {})
    owner = prop.get("ownerDetails", {})

    details = [
        f"**Full Details for: {prop.get('title', 'N/A')} [{property_id.upper()}]**",
        f"- **Listing:** For {prop.get('listingType', 'N/A').capitalize()} at **{price_str}**",
        f"- **Location:** {address.get('street', 'N/A')}, {address.get('city', 'N/A')}, {address.get('state', 'N/A')}",
        f"- **Property Type:** {prop.get('propertyType', 'N/A').capitalize()}",
        f"- **Specifications:** {prop.get('bedrooms', 'N/A')} Bedrooms, {prop.get('bathrooms', 'N/A')} Bathrooms",
        f"- **Area:** {prop.get('area', 'N/A')} sq. ft.",
        f"- **Furnished:** {'Yes' if prop.get('furnished') else 'No'}",
        f"- **Amenities:** {', '.join(prop.get('amenities', ['None']))}",
        f"- **Description:** {prop.get('description', 'No description provided.').strip()}",
        f"- **Owner Contact:** {owner.get('name', 'N/A')} at {owner.get('phone', 'N/A')}"
    ]
    return "\n".join(details)

api_property_search_tool = FunctionTool.from_defaults(
    fn=search_properties_via_api,
    name="property_search_api",
    description="Use to search for a list of properties. Requires `listing_type` and `city`."
)

get_property_details_tool = FunctionTool.from_defaults(
    fn=get_property_details,
    name="get_property_details",
    description="Use to get all details for a *single* property using its ID from the search results (e.g., 'PROP1')."
)