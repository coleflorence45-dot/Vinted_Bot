# vinted.py
import requests
from config import VINTED_COOKIE

VINTED_API = "https://www.vinted.co.uk/api/v2/catalog/items"

session = requests.Session()

def get_session_cookie():
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-GB,en;q=0.9",
        "Referer": "https://www.vinted.co.uk/",
        "Cookie": VINTED_COOKIE
    })

def fetch_listings(keyword, max_price):
    params = {
        "search_text": keyword,
        "price_to": max_price,
        "order": "newest_first",
        "per_page": 20
    }
    try:
        response = session.get(VINTED_API, params=params)
        print(f"Status code: {response.status_code}")
        data = response.json()
        return data.get("items", [])
    except Exception as e:
        print(f"Error fetching listings: {e}")
        return []

def format_item(item):
    return {
        "id": item["id"],
        "title": item["title"],
        "price": item["price"],
        "url": f"https://www.vinted.co.uk/items/{item['id']}",
        "brand": item.get("brand_title", "Unknown"),
        "size": item.get("size_title", "?"),
        "photo": item.get("photo", {}).get("url", "")
    }