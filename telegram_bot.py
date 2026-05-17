import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

VERDICT_EMOJI = {"BUY": "✅", "MAYBE": "🤔", "SKIP": "❌"}

def send_alert(item: dict, verdict: dict = None):
    signals_text = " ".join(item["signals"]) if item.get("signals") else ""

    caption = (
        f"🛍️ *{item['title']}*\n"
        f"💰 £{item['price']:.2f}\n"
        f"👗 {item.get('brand', '?')} | Size: {item.get('size', '?')}\n"
        f"⭐ Condition: {item.get('condition', '?')}\n"
        f"👤 Seller: {item.get('seller', '?')} ({item.get('seller_rep', '?')} feedback)\n"
    )

    if signals_text:
        caption += f"✅ {signals_text}\n"

    if verdict and verdict.get("verdict"):
        v = verdict["verdict"]
        emoji = VERDICT_EMOJI.get(v, "❓")
        caption += f"\n{emoji} *{v}*\n{verdict.get('summary', '')}\n"
        if verdict.get("expected_sell"):
            caption += (
                f"Expect: £{verdict.get('expected_sell', '?')} · "
                f"{verdict.get('expected_days', '?')}d\n"
            )
        if verdict.get("tip"):
            caption += f"💡 {verdict['tip']}\n"

    caption += f"\n🔗 {item['url']}"

    photo_url = item.get("photo", "")

    if photo_url:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "Markdown"
        }
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": caption,
            "parse_mode": "Markdown"
        }

    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[telegram] Failed to send alert: {e}")