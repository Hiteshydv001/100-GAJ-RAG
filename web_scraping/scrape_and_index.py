import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque

# --- Main Configuration Class ---
# All settings are in one place for easy modification.
class Config:
    BASE_URL = "https://100gaj.vercel.app/"
    # The domain name to stay within. Automatically derived from BASE_URL.
    ALLOWED_DOMAIN = urlparse(BASE_URL).netloc
    
    # Crawler settings
    MAX_PAGES_TO_SCRAPE = 50
    WAIT_TIME_PER_PAGE = 2  # Seconds to wait for JS to load
    HEADLESS_MODE = True # Set to False to watch the browser work (good for debugging)
    
    # Output file
    OUTPUT_JSON_FILE = "website_data_structured.json"
    
    # Patterns for URLs to avoid crawling.
    BLACKLISTED_PATTERNS = [
        "/verification",
        "/comingsoon",
        # Avoid non-essential utility pages
        "/legal",
        "/support",
        # Avoid generic search result pages with no specific content
        "/search?location="
    ]
    
    # Patterns for URLs that indicate a specific page type.
    # The order matters: the first match will be used.
    PAGE_TYPE_PATTERNS = {
        "property": [r"/search/[a-zA-Z0-9]+"],
        "agent_profile": [r"/agents/[a-zA-Z0-9]+"],
        "builder_profile": [r"/builders/[a-zA-Z0-9]+"],
        "agents_list": ["/agents"],
        "builders_list": ["/builders"],
        "generic": ["/"] # Fallback for any other page
    }

# --- Utility Functions ---

def setup_driver():
    """Sets up the Selenium WebDriver."""
    print("Setting up Chrome WebDriver...")
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    if Config.HEADLESS_MODE:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--log-level=3")
    options.add_argument("--blink-settings=imagesEnabled=false") # Disable images for speed
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def is_valid_url(url, visited_urls):
    """Checks if a URL is valid for crawling."""
    parsed_url = urlparse(url)
    # 1. Must be on the same domain
    if parsed_url.netloc != Config.ALLOWED_DOMAIN:
        return False
    # 2. Must not have been visited
    if url in visited_urls:
        return False
    # 3. Must not be a link to a file
    if any(url.endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.zip', '.webp']):
        return False
    # 4. Must not be in the blacklist
    if any(pattern in url for pattern in Config.BLACKLISTED_PATTERNS):
        return False
    return True

def get_page_type(url):
    """Determines the page type based on URL patterns."""
    path = urlparse(url).path
    for page_type, patterns in Config.PAGE_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, path):
                return page_type
    return "generic" # Default if no other pattern matches

# --- Page Type Specific Parsers ---
# These functions know how to extract structured data from specific page layouts.
# NOTE: These selectors are based on your provided HTML and may need to be adjusted
# if the website's structure changes.

def parse_property_page(soup):
    """Extracts structured data from a property details page."""
    data = {}
    # Find the main title/address
    title_el = soup.select_one('h1, h2, div[class*="property-title"]') # More flexible selector
    data['title'] = title_el.get_text(strip=True) if title_el else "N/A"
    
    # Find key specs - this requires inspecting the page's HTML
    specs = {}
    spec_container = soup.find('div', text=re.compile("Property Overview"))
    if spec_container:
      # This is a generic way to find key-value pairs.
      for item in spec_container.find_next_siblings('div'):
          key_el = item.find('span', {'class': 'key'})
          val_el = item.find('span', {'class': 'value'})
          if key_el and val_el:
              specs[key_el.text.strip()] = val_el.text.strip()
    
    # A more direct way based on your sample output
    bedrooms_el = soup.find('div', text=re.compile("Bedrooms"))
    if bedrooms_el:
        specs['Bedrooms'] = bedrooms_el.find_next('div').get_text(strip=True)

    data['specifications'] = specs

    price_el = soup.select_one('div[class*="price"], span[class*="price"]')
    if price_el:
        # Clean up price string: "₹4,000,000" -> 4000000
        price_text = price_el.get_text(strip=True)
        data['price'] = int(re.sub(r'[^\d]', '', price_text))
    
    description_el = soup.find('div', text=re.compile("Property Overview"))
    if description_el:
        data['description'] = description_el.find_next('p').get_text(separator=' ', strip=True)

    return {"type": "property", "data": data}

def parse_generic_page(soup):
    """Extracts the main text content from a generic page."""
    main_content = soup.find('main') or soup.body
    text = main_content.get_text(separator=' ', strip=True)
    return {"type": "generic", "data": {"text": text}}

# --- Main Scraper & Crawler Logic ---

def scrape_and_process_page(driver, url):
    """Drives the scraping of a single page and calls the correct parser."""
    try:
        driver.get(url)
        time.sleep(Config.WAIT_TIME_PER_PAGE)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        page_type = get_page_type(url)
        print(f"  -> Page type detected as: '{page_type}'")

        if page_type == "property":
            structured_data = parse_property_page(soup)
        # Add more parsers here if needed
        # elif page_type == "agent_profile":
        #     structured_data = parse_agent_page(soup)
        else:
            structured_data = parse_generic_page(soup)
        
        # Add universal data
        structured_data['url'] = url
        structured_data['title'] = soup.title.string if soup.title else "No Title"

        # Find all valid links for the crawler to follow
        links_on_page = {urljoin(url, a['href']) for a in soup.find_all('a', href=True)}
        return structured_data, links_on_page

    except Exception as e:
        print(f"  -! Critical error scraping {url}: {e}")
        return None, set()

if __name__ == "__main__":
    driver = setup_driver()
    urls_to_visit = deque([Config.BASE_URL])
    visited_urls = set()
    all_scraped_data = []

    print(f"\n🚀 Starting Power-Scrape on '{Config.ALLOWED_DOMAIN}'...")
    try:
        while urls_to_visit and len(visited_urls) < Config.MAX_PAGES_TO_SCRAPE:
            current_url = urls_to_visit.popleft()
            
            # Clean up URL (remove fragments like #)
            current_url = urlparse(current_url)._replace(fragment="").geturl()

            if not is_valid_url(current_url, visited_urls):
                continue
            
            print(f"\n[{len(visited_urls) + 1}/{Config.MAX_PAGES_TO_SCRAPE}] Scraping: {current_url}")
            visited_urls.add(current_url)

            page_data, new_links = scrape_and_process_page(driver, current_url)
            
            if page_data:
                all_scraped_data.append(page_data)
                for link in new_links:
                    if is_valid_url(link, visited_urls.union(set(urls_to_visit))):
                        urls_to_visit.append(link)
    
    finally:
        print("\n✅ Crawl finished or limit reached.")
        with open(Config.OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_scraped_data, f, ensure_ascii=False, indent=4)
        print(f"💾 Successfully saved structured data from {len(all_scraped_data)} pages to '{Config.OUTPUT_JSON_FILE}'")
        driver.quit()