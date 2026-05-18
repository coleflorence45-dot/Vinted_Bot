# advisor.py
import json
import base64
import requests
import os
from PIL import Image
import io

HISTORY_FILE = "dress_history.json"
ANTHROPIC_API = "https://api.anthropic.com/v1/messages"

_history_image_cache = {}

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def compress_image_b64(url: str):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content))
        img = img.convert("RGB")
        img.thumbnail((512, 512))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=70)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"[advisor] Could not fetch/compress image: {e}")
        return None

def get_cached_image(url: str):
    if url not in _history_image_cache:
        _history_image_cache[url] = compress_image_b64(url)
    return _history_image_cache[url]

def call_claude(model, system, content, max_tokens=150):
    from config import ANTHROPIC_API_KEY
    resp = requests.post(
        ANTHROPIC_API,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        },
        json={
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": content}]
        },
        timeout=30
    )
    resp.raise_for_status()
    raw = resp.json()["content"][0]["text"].strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def get_verdict(item: dict) -> dict:
    from config import ANTHROPIC_API_KEY
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith("sk-ant-your"):
        return {}

    # Fast title reject before any API call
    title_lower = item.get("title", "").lower()
    fast_rejects = [
        "bodycon", "body con", "body-con", "straight", "shift",
        "pencil", "fitted", "denim", "cotton", "jersey", "knit",
        "bandage", "tube", "sheath", "column"
    ]
    if any(w in title_lower for w in fast_rejects):
        print(f"[advisor] Fast rejected: title contains banned style word")
        return {}

    history = load_history()
    photo_url = item.get("photo", "")

    listing_context = (
        f'Title: {item.get("title", "")}\n'
        f'Brand: {item.get("brand", "")}\n'
        f'Size: {item.get("size", "")}\n'
        f'Price: £{item.get("price", "")}\n'
        f'Condition: {item.get("condition", "")}\n'
    )

    history_summary = [
        {"name": d["name"], "price_sold": d.get("price_sold"), "notes": d.get("notes", "")}
        for d in history
    ]

    # --- STAGE 1: Cheap Haiku text pre-screen ---
    prescreen_system = (
        "You are a filter for a UK Vinted resale bot. "
        "Based on the listing text alone, decide if this is worth analysing further. "
        "Reject if: childrenswear, menswear, accessory, not a dress, straight/bodycon/fitted cut, "
        "or clearly unsuitable for resale at £25-40. "
        "Respond ONLY with valid JSON, no markdown: "
        '{"pass": true|false, "reason": "one short reason if false"}'
    )

    prescreen_content = [{"type": "text", "text": f"Listing:\n{listing_context}"}]

    try:
        prescreen = call_claude("claude-haiku-4-5", prescreen_system, prescreen_content, max_tokens=60)
        if not prescreen.get("pass", True):
            print(f"[advisor] Pre-screen rejected: {prescreen.get('reason', '')}")
            return {}
    except Exception as e:
        print(f"[advisor] Pre-screen error: {e}")

    # --- STAGE 2: Full visual analysis with Sonnet ---
    content = []

    if photo_url:
        img_b64 = compress_image_b64(photo_url)
        if img_b64:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}
            })
            content.append({"type": "text", "text": "[This is the NEW dress listing to evaluate]"})

    # Attach up to 3 cached history images
    if photo_url:
        for d in [x for x in history if x.get("image_url")][:3]:
            h_img = get_cached_image(d["image_url"])
            if h_img:
                sold = d.get("price_sold")
                content.append({
                    "type": "text",
                    "text": (
                        f'[HISTORY: "{d["name"]}" | '
                        f'{"Sold £" + str(sold) if sold else "Unsold"} | '
                        f'{str(d["days_to_sell"]) + "d" if d.get("days_to_sell") else "days unknown"} | '
                        f'{d.get("notes", "")}]'
                    )
                })
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": h_img}
                })

    content.append({
        "type": "text",
        "text": (
            f"Listing details:\n{listing_context}\n"
            f"Sales history:\n{json.dumps(history_summary) if history else 'No history yet — use general UK Vinted resale knowledge.'}"
        )
    })

    model = "claude-sonnet-4-5" if photo_url else "claude-haiku-4-5"

    system = (
        "You are a practical secondhand dress resale advisor for a UK Vinted seller. "
        "Analyse the new listing vs the buyer's history using visual and text similarity. "
        "When comparing images, focus ONLY on the dress itself — its silhouette, cut, fabric, "
        "print, pattern and colour. Completely ignore backgrounds, wallpaper, furniture, "
        "lighting or anything that is not the dress. "
        "The seller prefers flared, floaty, or full-skirted dresses — skater, fit-and-flare, "
        "wrap, midi with volume, or any style with movement. "
        "Always SKIP straight, bodycon, pencil, shift, fitted, jersey, or column dresses "
        "regardless of brand or price. "
        "Only sold prices are available in the history. "
        "Respond ONLY with compact valid JSON, no markdown:\n"
        '{"verdict":"BUY"|"SKIP"|"MAYBE","summary":"2 sentences max",'
        '"expected_sell":0,"expected_days":0,"tip":"one short practical tip"}'
    )

    try:
        return call_claude(model, system, content, max_tokens=150)
    except Exception as e:
        print(f"[advisor] Claude API error: {e}")
        return {}