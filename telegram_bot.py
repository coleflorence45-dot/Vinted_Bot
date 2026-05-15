# telegram_bot.py
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from bot_controls import pending_messages, get_keyboard
from datetime import datetime
import json

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
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(get_keyboard())
    }
    response = requests.post(url, json=payload)
    data = response.json()

    # Track the message for auto-delete
    if data.get("ok"):
        msg_id = data["result"]["message_id"]
        pending_messages[msg_id] = {
            "chat_id": TELEGRAM_CHAT_ID,
            "sent_time": datetime.now()
        }

def send_cookie_warning():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "⚠️ *Vinted bot has stopped working* — cookies have likely expired.\n\nOpen vinted.co.uk in Chrome, press F12, go to Console, type `document.cookie`, copy the result and update `config.py`.",
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)