# main.py
import time
import random
from config import SEARCH_KEYWORDS, CHECK_INTERVAL_SECONDS
from vinted import fetch_listings, format_item, get_session_cookie, passes_filters
from telegram_bot import send_alert
from tracker import load_seen, save_seen, is_new
from bot_controls import start_bot_thread

start_bot_thread()

get_session_cookie()

def seed_seen_items():
    """First run - silently save all current listings, send no alerts"""
    print("⏳ Seeding existing listings, no alerts will be sent...")
    seen_ids = load_seen()
    new_seen = set(seen_ids)
    for keyword in SEARCH_KEYWORDS:
        items = fetch_listings(keyword)
        for raw_item in items:
            new_seen.add(str(raw_item["id"]))
        time.sleep(random.uniform(1, 3))
    save_seen(new_seen)
    print(f"✅ Seeded {len(new_seen)} existing items. Now watching for NEW listings...\n")

def check_vinted():
    print("🔍 Checking Vinted...")
    seen_ids = load_seen()
    new_seen = set(seen_ids)
    found = 0

    for keyword in SEARCH_KEYWORDS:
        items = fetch_listings(keyword)
        for raw_item in items:
            if not is_new(raw_item["id"], seen_ids) or not is_new(raw_item["id"], new_seen):
                continue
            new_seen.add(str(raw_item["id"]))
            passed, reason = passes_filters(raw_item)
            if not passed:
                continue
            item = format_item(raw_item)
            print(f"  ✅ {item['title']} — £{item['price']:.2f}")
            send_alert(item)
            found += 1
        time.sleep(random.uniform(1, 3))  # random gap between keywords

    save_seen(new_seen)
    if found == 0:
        print("  No new matching listings found.")
    print("✅ Check complete.\n")

# Wipe seen list and seed on every startup
open("seen_items.txt", "w").close()
seed_seen_items()

print(f"👀 Checking every {CHECK_INTERVAL_SECONDS} seconds...\n")
while True:
    check_vinted()
    time.sleep(CHECK_INTERVAL_SECONDS)