# telegram_bot.py
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_alert(item):
    signals_text = "  ".join(item["signals"]) if item["signals"] else ""

    message = (
        f"🛍️ *{item['title']}*\n"
        f"💰 £{item['price']:.2f}\n"
        f"👗 {item['brand']}  |  Size: {item['size']}\n"
        f"⭐ Condition: {item['condition']}\n"
        f"👤 Seller: {item['seller']} ({item['seller_rep']} feedback)\n"
    )
    if signals_text:
        message += f"✅ {signals_text}\n"
    message += f"\n🔗 {item['url']}"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)