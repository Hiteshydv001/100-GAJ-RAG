# File: app/core/tools/api_property_search.py

import httpx
from llama_index.core.tools import FunctionTool
from typing import Optional
import certifi # Ensure this import is here

API_URL = "https://100gaj.vercel.app/api/properties"

def search_properties_via_api(
    listing_type: str,
    property_type: Optional[str] = None,
    city: Optional[str] = None
) -> str:
    """
    Searches for properties using the official 100Gaj API.
    """
    print(f"--- Executing API Search: type={listing_type}, property={property_type}, city={city} ---")
    
    if listing_type.lower() == 'buy':
        listing_type = 'sale'

    if listing_type.lower() not in ['sale', 'rent']:
        return "Error: Invalid listing_type. It must be either 'buy'/'sale' or 'rent'."

    params = {
        "listingType": listing_type.lower(),
    }
    if property_type:
        params["propertyType"] = property_type.lower()
    if city:
        params["address.city"] = city

    try:
        # This is the correct place for SSL handling
        ssl_context = httpx.create_ssl_context(verify=certifi.where())
        
        with httpx.Client(verify=ssl_context) as client:
            response = client.get(API_URL, params=params, timeout=20.0)
            response.raise_for_status()
            data = response.json()

        if not data.get("success") or not data.get("properties"):
            return f"No properties were found matching your criteria (Listing Type: {listing_type}, Property Type: {property_type}, City: {city})."

        properties = data["properties"]
        count = data.get("count", len(properties))

        formatted_results = []
        for prop in properties:
            address = prop.get("address", {})
            price = prop.get("price", "N/A")
            try:
                price_str = f"₹{price:,}"
            except (ValueError, TypeError):
                price_str = str(price)

            details = (
                f"- **Title:** {prop.get('title', 'N/A')}\n"
                f"  **Location:** {address.get('street', 'N/A')}, {address.get('city', 'N/A')}\n"
                f"  **Price:** {price_str}\n"
                f"  **Type:** {prop.get('propertyType', 'N/A')} for {prop.get('listingType', 'N/A')}\n"
                f"  **Details:** {prop.get('bedrooms', 'N/A')} Bedrooms, {prop.get('bathrooms', 'N/A')} Bathrooms, {prop.get('area', 'N/A')} sq. ft."
            )
            formatted_results.append(details)
        
        return f"Found {count} properties matching your search:\n\n" + "\n\n".join(formatted_results)

    except httpx.HTTPStatusError as e:
        return f"API Error: The server responded with status code {e.response.status_code}. Please try again later."
    except Exception as e:
        return f"An unexpected error occurred while fetching properties from the API: {str(e)}"

api_property_search_tool = FunctionTool.from_defaults(
    fn=search_properties_via_api,
    name="property_search_api",
    description=(
        "Use this tool to search for property listings via the official API. "
        "It REQUIRES a `listing_type` ('sale' or 'rent'). "
        "It can also optionally filter by `property_type` (e.g., 'apartment', 'villa', 'house', 'commercial') and `city`."
    )
)