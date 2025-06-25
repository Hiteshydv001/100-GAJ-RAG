import time
from typing import Optional, List, Dict
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

BASE_URL = "https://100gaj.vercel.app"

TARGET_ROUTES = [
    {"location": "delhi", "filter_": "sale", "propertyType": None},
    {"location": "delhi", "filter_": "rent", "propertyType": None},
    {"location": "delhi", "filter_": "sale", "propertyType": "Flat"},
    {"location": "delhi", "filter_": "sale", "propertyType": "Apartment"},
    {"location": "delhi", "filter_": "sale", "propertyType": "Villa"},
    {"location": "delhi", "filter_": "sale", "propertyType": "Commercial"},
]

def build_url(location: str, filter_: str, propertyType: Optional[str] = None) -> str:
    params = {"location": location, "filter": filter_}
    if propertyType:
        params["propertyType"] = propertyType
    return f"{BASE_URL}/search?{urlencode(params)}"

def parse_properties(html: str, expected_type: Optional[str] = None) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select("div[id^='property-']")
    properties = []

    for card in cards:
        try:
            title = card.select_one("h3").get_text(strip=True)
            loc = card.select_one("p.text-xs").get_text(strip=True)
            price = card.select_one("div.text-orange-500").get_text(strip=True)
            detail_div = card.select_one("div.mt-3.flex.items-center")
            tag = card.select_one("div.rounded-full") or card.select_one("div:has(svg)")
            tag_text = tag.get_text(strip=True) if tag else "Unknown"

            if expected_type and tag_text.lower() != expected_type.lower():
                continue

            details = ' | '.join(
                d.get_text(strip=True) for d in detail_div.find_all('div', recursive=False)
            ) if detail_div else "N/A"

            properties.append({
                "title": title,
                "location": loc,
                "price": price,
                "type": tag_text,
                "details": details,
            })

        except Exception as e:
            print(f"[⚠️] Failed to parse one property card: {e}")
    return properties

def scrape_route(location: str, filter_: str, propertyType: Optional[str] = None):
    url = build_url(location, filter_, propertyType)
    print(f"\n🔍 Scraping: {url}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(4000)
            page.wait_for_selector("div.space-y-4", timeout=15000)
            html = page.content()
            browser.close()

        listings = parse_properties(html, expected_type=propertyType)

        if listings:
            print(f"✅ Found {len(listings)} properties for: {url}")
            for i, prop in enumerate(listings, 1):
                print(
                    f"\n🏠 Property #{i}\n"
                    f"📌 {prop['title']}\n"
                    f"📍 {prop['location']}\n"
                    f"💰 {prop['price']}\n"
                    f"🏷️ {prop['type']}\n"
                    f"📐 {prop['details']}\n"
                )
        else:
            print(f"⚠️ No properties found for: {url}")

    except Exception as e:
        print(f"❌ Failed to scrape {url}: {e}")

# --- Run all routes ---
if __name__ == "__main__":
    print("🚀 Starting property scraping for 100gaj...")
    for route in TARGET_ROUTES:
        scrape_route(**route)
        time.sleep(1)  # avoid hammering the server
