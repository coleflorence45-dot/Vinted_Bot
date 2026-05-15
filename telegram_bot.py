import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_alert(item):
    message = (
        f"🛍️ *{item['title']}*\n"
        f"💰 Price: £{item['price']}\n"
        f"👗 Brand: {item['brand']} | Size: {item['size']}\n"
        f"🔗 {item['url']}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)