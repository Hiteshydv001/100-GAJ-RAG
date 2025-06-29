import httpx
from llama_index.core.tools import FunctionTool
from typing import Optional, List, Dict, Union
import certifi
from functools import lru_cache
import re
import json # Import json for pretty printing

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

def format_price(price: Union[int, float, str]) -> str:
    """Helper function to format price in Crores/Lakhs format."""
    if not isinstance(price, (int, float)):
        return str(price)
    
    if price >= 10000000:  # 1 Crore = 10000000
        crores = price / 10000000
        return f"₹{crores:.2f} Crores"
    else:
        lakhs = price / 100000
        return f"₹{lakhs:.2f} Lakhs"

def format_area(area: Union[int, float, str], unit: str = "") -> str:
    """Format area with appropriate unit."""
    try:
        if isinstance(area, str):
            return f"{area} {unit}".strip()
        return f"{area:,} {unit}".strip()
    except:
        return str(area)

def clean_description(desc: str) -> str:
    """Helper function to clean and format property descriptions."""
    if not isinstance(desc, str):
        return "No description available."
    
    # Remove markdown and unwanted formatting
    cleaned_desc = re.sub(r'(\n|^)##.*', '', desc)
    cleaned_desc = re.sub(r'(\n|^)###.*', '', cleaned_desc)
    cleaned_desc = re.sub(r'(\n|^)\*\*.*?\*\*', '', cleaned_desc)
    
    # Remove common introductory phrases
    phrases_to_remove = [
        "Here is a compelling real estate property description:",
        "Here is the rewritten description, within the 150-word limit:",
        "Here is a rewritten description that is under 150 words and highlights the property's features and benefits:",
        "Here's a compelling real estate property description for the Luxury apartment:",
        "Here is a rewritten version with some improvements:",
        "Here is the final version:",
        "Let me know if you need any further adjustments!"
    ]
    for phrase in phrases_to_remove:
        cleaned_desc = cleaned_desc.replace(phrase, '')
        
    return cleaned_desc.strip()

def query_property_database(
    city: Optional[str] = None,
    listing_type: Optional[Union[str, List[str]]] = None,
    property_type: Optional[str] = None
) -> str:
    """
    Searches the in-memory property database based on provided filters.
    Handles Delhi properties with special care, checking both city and state fields.
    """
    all_properties = _fetch_all_data()
    if not all_properties:
        return "I apologize, but I'm unable to access the property database at the moment. Please try again in a few moments."

    results = all_properties

    # INTELLIGENT CITY/STATE FILTERING
    if city:
        city_lower = city.lower()
        if city_lower == "delhi":
            # Special handling for Delhi - check both city and state
            results = [p for p in results if 
                      (p.get("address", {}).get("city", "").lower() == city_lower) or
                      (p.get("address", {}).get("state", "").lower() == city_lower) or
                      (p.get("address", {}).get("street", "").lower().find(city_lower) != -1)]
        else:
            results = [p for p in results if 
                      p.get("address", {}).get("city", "").lower() == city_lower]

    if listing_type:
        if isinstance(listing_type, str):
            listing_type_filters = [listing_type.lower().replace("buy", "sale")]
        else:
            listing_type_filters = [lt.lower().replace("buy", "sale") for lt in listing_type]
        results = [p for p in results if p.get("listingType", "").lower() in listing_type_filters]

    if property_type:
        results = [p for p in results if p.get("propertyType", "").lower() == property_type.lower()]

    if not results:
        suggestions = ""
        if city:
            suggestions = " Try searching in other nearby areas or adjusting your search criteria."
        return f"I could not find any properties matching your criteria.{suggestions}"

    # Format results
    formatted_results = []
    for prop in results[:5]:
        address = prop.get("address", {})
        price = prop.get("price", 0)
        
        # Format price in Lakhs/Crores
        if isinstance(price, (int, float)):
            if price >= 10000000:  # 1 Crore = 10000000
                price_str = f"₹{price/10000000:.2f} Crores"
            else:
                price_str = f"₹{price/100000:.2f} Lakhs"
        else:
            price_str = str(price)

        # Location details
        street = address.get("street", "").strip()
        city = address.get("city", "").strip()
        state = address.get("state", "").strip()
        location_parts = [p for p in [street, city, state] if p]
        location = ", ".join(location_parts) if location_parts else "Location not specified"

        # Property details
        details = [
            f"\n🏠 Property Details:",
            f"Title: {prop.get('title', 'N/A')}",
            f"Location: {location}",
            f"Price: {price_str}",
            f"Type: {prop.get('propertyType', 'N/A').capitalize()}",
            f"Configuration: {prop.get('bedrooms', 'N/A')} BHK, {prop.get('bathrooms', 'N/A')} Bath",
            f"Area: {prop.get('area', 'N/A')} sq ft",
            f"Status: {'Furnished' if prop.get('furnished') else 'Unfurnished'}",
            f"Available for: {prop.get('listingType', 'N/A').upper()}"
        ]

        # Add amenities if available
        amenities = prop.get("amenities", [])
        if amenities:
            details.append(f"Amenities: {', '.join(amenities)}")

        # Add contact information
        owner = prop.get("ownerDetails", {})
        if owner:
            details.extend([
                "\n📞 Contact Information:",
                f"Owner: {owner.get('name', 'N/A')}",
                f"Phone: {owner.get('phone', 'N/A')}"
            ])

        formatted_results.append("\n".join(details))

    return "\n\n" + "\n\n---\n\n".join(formatted_results)

# Create the tool with clear description and parameters
property_database_tool = FunctionTool.from_defaults(
    fn=query_property_database,
    name="query_property_database",
    description="Use this to find and list properties. You can filter by `city`, `listing_type` (sale/rent), and `property_type`."
)