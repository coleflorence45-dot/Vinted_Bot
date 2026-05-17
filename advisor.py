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
    """Download a photo URL and return base64-encoded JPEG string."""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return base64.b64encode(r.content).decode("utf-8")
    except Exception as e:
        print(f"[advisor] Could not fetch image: {e}")
        return None

def get_verdict(item: dict) -> dict:
    """
    Analyse a Vinted listing against purchase history using Claude.
    Returns a verdict dict with keys: verdict, summary, max_to_pay, expected_sell, expected_days, tip
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[advisor] ANTHROPIC_API_KEY not set — skipping analysis")
        return {}

    history = load_history()

    # Build message content
    content = []

    # Attach the listing photo if available
    photo_url = item.get("photo", "")
    if photo_url:
        img_b64 = fetch_image_b64(photo_url)
        if img_b64:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}
            })
            content.append({"type": "text", "text": "[This is the NEW dress listing to evaluate]"})

    # Attach history images (up to 6)
    for d in [x for x in history if x.get("image_url")][:6]:
        h_img = fetch_image_b64(d["image_url"])
        if h_img:
            profit = round(d["price_sold"] - d["price_bought"], 2) if d.get("price_sold") else None
            content.append({
                "type": "text",
                "text": (
                    f'[HISTORY: "{d["name"]}" | '
                    f'Bought £{d["price_bought"]} | '
                    f'{"Sold £" + str(d["price_sold"]) + " (profit £" + str(profit) + ")" if profit is not None else "Unsold"} | '
                    f'{str(d["days_to_sell"]) + "d" if d.get("days_to_sell") else "days unknown"}]'
                )
            })
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": h_img}
            })

    # History context as JSON for text-only comparison too
    history_summary = [
        {
            "name": d["name"],
            "price_bought": d["price_bought"],
            "price_sold": d.get("price_sold"),
            "profit": round(d["price_sold"] - d["price_bought"], 2) if d.get("price_sold") else None,
            "days_to_sell": d.get("days_to_sell"),
            "notes": d.get("notes", "")
        }
        for d in history
    ]

    listing_context = (
        f'Title: {item.get("title", "")}\n'
        f'Brand: {item.get("brand", "")}\n'
        f'Size: {item.get("size", "")}\n'
        f'Price: £{item.get("price", "")}\n'
        f'Condition: {item.get("condition", "")}\n'
    )

    history_text = json.dumps(history_summary) if history else "No history yet — use general resale knowledge."

    content.append({
        "type": "text",
        "text": f"Listing details:\n{listing_context}\nFull purchase history:\n{history_text}"
    })

    system = (
        "You are a practical secondhand dress resale advisor. "
        "Analyse the new Vinted listing against the buyer's history using visual and text similarity. "
        "Respond ONLY with compact valid JSON, no markdown:\n"
        '{"verdict":"BUY"|"SKIP"|"MAYBE","summary":"2 sentences max",'
        '"max_to_pay":0,"expected_sell":0,"expected_days":0,"tip":"one short tip"}'
    )

    try:
        resp = requests.post(
            ANTHROPIC_API,
            headers={"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 500,
                "system": system,
                "messages": [{"role": "user", "content": content}]
            },
            timeout=30
        )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[advisor] Claude API error: {e}")
        return {}