import json
import base64
import requests
import os

HISTORY_FILE = "dress_history.json"
ANTHROPIC_API = "https://api.anthropic.com/v1/messages"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def fetch_image_b64(url: str) -> str | None:
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return base64.b64encode(r.content).decode("utf-8")
    except Exception as e:
        print(f"[advisor] Could not fetch image: {e}")
        return None

def get_verdict(item: dict) -> dict:
    from config import ANTHROPIC_API_KEY
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith("sk-ant-your"):
        print("[advisor] No API key set — skipping analysis")
        return {}

    history = load_history()
    content = []

    photo_url = item.get("photo", "")
    if photo_url:
        img_b64 = fetch_image_b64(photo_url)
        if img_b64:
            content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}})
            content.append({"type": "text", "text": "[This is the NEW dress listing to evaluate]"})

    for d in [x for x in history if x.get("image_url")][:6]:
        h_img = fetch_image_b64(d["image_url"])
        if h_img:
            sold = d.get("price_sold")
            content.append({"type": "text", "text": f'[HISTORY: "{d["name"]}" | {"Sold £" + str(sold) if sold else "Unsold"} | {str(d["days_to_sell"]) + "d" if d.get("days_to_sell") else "days unknown"}]'})
            content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": h_img}})

    history_summary = [{"name": d["name"], "price_sold": d.get("price_sold"), "notes": d.get("notes", "")} for d in history]

    listing_context = (
        f'Title: {item.get("title", "")}\n'
        f'Brand: {item.get("brand", "")}\n'
        f'Size: {item.get("size", "")}\n'
        f'Price: £{item.get("price", "")}\n'
        f'Condition: {item.get("condition", "")}\n'
    )

    content.append({
        "type": "text",
        "text": f"Listing:\n{listing_context}\nHistory:\n{json.dumps(history_summary) if history else 'No history yet.'}"
    })

    system = (
        "You are a practical secondhand dress resale advisor for a UK Vinted seller. "
        "Analyse the new listing vs history visually and by text. Only sold prices available. "
        "When comparing images, focus ONLY on the dress itself — its silhouette, cut, fabric, "
        "print, pattern and colour. Completely ignore backgrounds, wallpaper, furniture, "
        "lighting or anything that is not the dress. "
        "Respond ONLY with compact valid JSON, no markdown:\n"
        '{"verdict":"BUY"|"SKIP"|"MAYBE","summary":"2 sentences","expected_sell":0,"expected_days":0,"tip":"one short tip"}'
    )

    try:
        resp = requests.post(
            ANTHROPIC_API,
            headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 500, "system": system, "messages": [{"role": "user", "content": content}]},
            timeout=30
        )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[advisor] Claude API error: {e}")
        return {}