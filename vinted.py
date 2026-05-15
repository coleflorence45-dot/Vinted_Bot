# vinted.py
from curl_cffi import requests as cffi_requests
from config import (
    VINTED_COOKIE, MIN_PRICE, MAX_PRICE,
    GOOD_CONDITIONS, BAD_TITLE_KEYWORDS,
    MIN_SELLER_REPUTATION, REQUIRED_BRANDS, 
    BRAND_EXEMPT_KEYWORDS
)

VINTED_API = "https://www.vinted.co.uk/api/v2/catalog/items"

session = cffi_requests.Session(impersonate="chrome120")

def get_session_cookie():
    session.headers.update({
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-GB,en;q=0.9",
        "Referer": "https://www.vinted.co.uk/",
        "Cookie": VINTED_COOKIE
    })

def fetch_listings(keyword):
    params = {
        "search_text": keyword,
        "price_from": MIN_PRICE,
        "price_to": MAX_PRICE,
        "order": "newest_first",
        "per_page": 30
    }
    try:
        response = session.get(VINTED_API, params=params)
        if response.status_code == 403:
            print("  ⚠️ Cookie expired — sending Telegram warning")
            from telegram_bot import send_cookie_warning
            send_cookie_warning()
            return []
        if response.status_code != 200:
            print(f"  ⚠️ Bad status {response.status_code} for '{keyword}'")
            return []
        data = response.json()
        return data.get("items", [])
    except Exception as e:
        print(f"  ⚠️ Error fetching '{keyword}': {e}")
        return []

def passes_filters(item):
    title = item.get("title", "").lower()

    # Check brand whitelist
    brand = item.get("brand_title", "").lower()
    if not any(b in brand for b in REQUIRED_BRANDS):
        return False, f"Brand not in whitelist: {brand}"
    
    brand_exempt = any(kw in title for kw in BRAND_EXEMPT_KEYWORDS)
    if not brand_exempt and not any(b in brand for b in REQUIRED_BRANDS):
        return False, f"Brand not in whitelist: {brand}"

    # Check condition
    condition = item.get("status", "").lower()
    if not any(good in condition for good in GOOD_CONDITIONS):
        return False, f"Condition: {condition}"

    # Check for bad words in title
    for bad_word in BAD_TITLE_KEYWORDS:
        if bad_word in title:
            return False, f"Bad keyword: '{bad_word}'"

    # Check seller reputation
    user = item.get("user", {})
    reputation = user.get("feedback_reputation", 1.0)
    if reputation is not None and float(reputation) < MIN_SELLER_REPUTATION:
        return False, f"Low reputation: {reputation}"

    return True, "OK"

def format_item(item):
    title = item.get("title", "")
    price = float(item["price"]["amount"])

    signals = []
    combined = title.lower() + " " + item.get("description", "").lower()
    if item.get("user", {}).get("bundle_discount") is not None:
        signals.append("🛍️ Bundle deals")
    if any(s in combined for s in ["bnwt", "brand new", "never worn", "unworn"]):
        signals.append("✨ Never worn")

    condition = item.get("status", "Unknown")
    seller = item.get("user", {})
    seller_name = seller.get("login", "Unknown")
    seller_rep = seller.get("feedback_reputation", "?")
    seller_rep_pct = f"{float(seller_rep)*100:.0f}%" if seller_rep != "?" else "?"

    return {
        "id": item["id"],
        "title": title,
        "price": price,
        "url": f"https://www.vinted.co.uk/items/{item['id']}",
        "brand": item.get("brand_title", "Unknown"),
        "size": item.get("size_title", "Any"),
        "condition": condition,
        "seller": seller_name,
        "seller_rep": seller_rep_pct,
        "signals": signals,
    }