import schedule
import time
from config import SEARCH_KEYWORDS, MAX_PRICE, CHECK_INTERVAL_MINUTES
from vinted import fetch_listings, format_item, get_session_cookie
from telegram_bot import send_alert
from tracker import load_seen, save_seen, is_new

get_session_cookie()

def check_vinted():
    print("🔍 Checking Vinted...")
    seen_ids = load_seen()
    new_seen = set(seen_ids)

    for keyword in SEARCH_KEYWORDS:
        items = fetch_listings(keyword, MAX_PRICE)
        for raw_item in items:
            passed, reason = passes_filters(raw_item)
            if not passed:
                continue  # silently skip
            item = format_item(raw_item)
            if is_new(item["id"], seen_ids):
                print(f"  ✅ {item['title']} — £{item['price']:.2f}")
                send_alert(item)
                new_seen.add(str(item["id"]))
                

    save_seen(new_seen)
    print("✅ Check complete.\n")

# Run once immediately, then every 5 minutes
check_vinted()
schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(check_vinted)

while True:
    schedule.run_pending()
    time.sleep(30)