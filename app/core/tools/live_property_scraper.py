from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from llama_index.core.tools import FunctionTool
from typing import Optional
from urllib.parse import urlencode

BASE_URL = "https://100gaj.vercel.app/search"

def search_properties_from_website(location: str, property_status: str, property_type: Optional[str] = None) -> str:
    """
    Searches for property listings by scraping the 100gaj.vercel.app website.
    It requires a location and a status ('sale' or 'rent'), and can optionally filter by property type.
    """
    print("--- Initializing Synchronous Playwright Scraper Tool ---")
    
    with sync_playwright() as p:
        try:
            status_lower = 'sale' if property_status.lower() == 'buy' else property_status.lower()
            if status_lower not in ["sale", "rent"]:
                return "Error: Invalid property_status. It must be either 'sale' or 'rent'."

            params = {"location": location, "filter": status_lower}
            if property_type:
                params["propertyType"] = property_type

            query_string = urlencode(params)
            search_url = f"{BASE_URL}?{query_string}"
            print(f"Scraping URL: {search_url}")

            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(search_url, wait_until="networkidle", timeout=30000)
            
            card_selector = "div.bg-gray-900" 
            page.wait_for_selector(card_selector, timeout=15000)
            
            html_content = page.content()
            browser.close()

            soup = BeautifulSoup(html_content, 'lxml')
            property_cards = soup.select(card_selector)

            if not property_cards:
                type_str = f"a '{property_type}'" if property_type else "any"
                return f"No {type_str} properties were found for '{status_lower}' in '{location}' on the website."

            extracted_listings = []
            for card in property_cards:
                title = card.find('h3').text.strip() if card.find('h3') else "N/A"
                location_text = card.find('p', class_='text-xs').text.strip() if card.find('p', class_='text-xs') else "N/A"
                price = card.find('div', class_='text-orange-500').text.strip() if card.find('div', class_=['text-orange-500']) else "N/A"
                details = ' | '.join(tag.text.strip() for tag in card.find_all('div', class_='flex items-center mr-3'))
                extracted_listings.append(f"- Title: {title}\n  Location: {location_text}\n  Price/Rent: {price}\n  Details: {details}")
            
            return f"Found {len(extracted_listings)} properties on 100gaj.vercel.app:\n" + "\n".join(extracted_listings)

        except Exception as e:
            # --- FIX: Ensure the error message is always a string ---
            return f"An error occurred during scraping: {str(e)}"

# --- Create a single, powerful LlamaIndex Tool Object ---
live_property_search_tool = FunctionTool.from_defaults(
    fn=search_properties_from_website,
    name="property_search_tool",
    description=(
        "Use this tool to search the 100gaj.vercel.app website for property listings. "
        "It requires a `location` and a `property_status` ('sale' or 'rent'). "
        "It can also optionally filter by a `property_type` ('Flat', 'Apartment', 'Villa', 'Commercial'). "
        "DO NOT use this tool if you are missing the `location` or `property_status`."
    )
)