"""
history.py — manage your dress purchase history

Usage:
  python history.py add     — log a past dress interactively
  python history.py list    — view all logged dresses
  python history.py stats   — show summary stats
"""

import json
import os
import sys
from datetime import datetime

HISTORY_FILE = "dress_history.json"

def load():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def save(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def prompt(label, required=False, cast=None, default=None):
    suffix = " (required)" if required else f" [enter to skip]" if default is None else f" [default: {default}]"
    while True:
        raw = input(f"  {label}{suffix}: ").strip()
        if not raw:
            if required:
                print("  ⚠️  This field is required.")
                continue
            return default
        if cast:
            try:
                return cast(raw)
            except ValueError:
                print(f"  ⚠️  Please enter a valid {cast.__name__}.")
                continue
        return raw

def cmd_add():
    print("\n📝 Log a past dress purchase\n")
    history = load()

    name = prompt("Dress name / description", required=True)
    image_url = prompt("Photo URL (from Vinted listing, optional)")
    price_bought = prompt("Price bought (£)", required=True, cast=float)

    sold = input("  Did it sell? [y/n]: ").strip().lower()
    price_sold = None
    days_to_sell = None
    if sold == "y":
        price_sold = prompt("Price sold (£)", cast=float)
        days_to_sell = prompt("Days to sell", cast=int)

    notes = prompt("Notes (optional)")

    entry = {
        "id": len(history) + 1,
        "name": name,
        "image_url": image_url or "",
        "price_bought": price_bought,
        "price_sold": price_sold,
        "days_to_sell": days_to_sell,
        "notes": notes or "",
        "date_added": datetime.now().strftime("%Y-%m-%d")
    }

    history.append(entry)
    save(history)

    profit = f"+£{price_sold - price_bought:.2f}" if price_sold else "unsold"
    print(f"\n✅ Saved: {name} — bought £{price_bought:.2f}, {profit}\n")

def cmd_list():
    history = load()
    if not history:
        print("\nNo dresses logged yet. Run: python history.py add\n")
        return
    print(f"\n{'#':<4} {'Name':<35} {'Bought':>8} {'Sold':>8} {'Profit':>8} {'Days':>6}")
    print("-" * 75)
    for d in history:
        profit = f"+£{d['price_sold'] - d['price_bought']:.0f}" if d.get("price_sold") else "unsold"
        sold = f"£{d['price_sold']:.0f}" if d.get("price_sold") else "—"
        days = str(d["days_to_sell"]) if d.get("days_to_sell") else "—"
        print(f"{d['id']:<4} {d['name'][:34]:<35} £{d['price_bought']:<7.0f} {sold:>8} {profit:>8} {days:>6}")
    print()

def cmd_stats():
    history = load()
    if not history:
        print("\nNo history yet.\n")
        return
    sold = [d for d in history if d.get("price_sold") is not None]
    profits = [d["price_sold"] - d["price_bought"] for d in sold]
    days_list = [d["days_to_sell"] for d in history if d.get("days_to_sell")]

    print(f"\n📊 History stats ({len(history)} dresses)")
    print(f"  Sold:        {len(sold)} / {len(history)}")
    if profits:
        print(f"  Avg profit:  £{sum(profits)/len(profits):.2f}")
        print(f"  Best:        £{max(profits):.2f}  |  Worst: £{min(profits):.2f}")
    if days_list:
        print(f"  Avg days:    {sum(days_list)/len(days_list):.0f}d")
    print()

COMMANDS = {"add": cmd_add, "list": cmd_list, "stats": cmd_stats}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    if cmd not in COMMANDS:
        print(__doc__)
    else:
        COMMANDS[cmd]()