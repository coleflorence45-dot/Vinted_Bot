# telegram_bot.py
import requests
import json
from datetime import datetime
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from bot_controls import pending_messages, get_keyboard

VERDICT_EMOJI = {"BUY": "✅", "MAYBE": "🤔", "SKIP": "❌"}

def send_alert(item, verdict=None):
    signals_text = "  ".join(item["signals"]) if item["signals"] else ""

    # Verdict line
    if verdict and verdict.get("verdict"):
        v = verdict["verdict"]
        emoji = VERDICT_EMOJI.get(v, "❓")
        verdict_line = f"{emoji} *{v}*  ·  £{verdict.get('expected_sell', '?')} est.  ·  {verdict.get('expected_days', '?')}d\n"
        tip_line = f"💡 _{verdict.get('tip', '')}_\n" if verdict.get("tip") else ""
    else:
        verdict_line = ""
        tip_line = ""

    text = (
        f"🛍️ *{item['title']}*  ·  £{item['price']:.2f}\n"
        f"👗 {item['brand']}  ·  {item['size']}  ·  {item['condition']}\n"
    )

    if signals_text:
        text += f"✅ {signals_text}\n"

    text += f"\n{verdict_line}{tip_line}"
    text += f"🔗 {item['url']}"

    photo_url = item.get("photo", "")

    if photo_url:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": photo_url,
            "caption": text[:1024],
            "parse_mode": "Markdown",
            "reply_markup": json.dumps(get_keyboard())
        }
    else:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": json.dumps(get_keyboard())
        }

    response = requests.post(api_url, json=payload)
    data = response.json()

    if data.get("ok"):
        msg_id = data["result"]["message_id"]
        pending_messages[msg_id] = {
            "chat_id": TELEGRAM_CHAT_ID,
            "sent_time": datetime.now(),
            "is_photo": bool(photo_url)
        }

def send_cookie_warning():
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": (
            "⚠️ *Vinted bot has stopped working* — cookies have likely expired.\n\n"
            "Open vinted.co.uk in Chrome, press F12, go to Console, "
            "type `document.cookie`, copy the result and update `config.py`."
        ),
        "parse_mode": "Markdown"
    }
    requests.post(api_url, data=payload)