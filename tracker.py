import os

SEEN_FILE = "seen_items.txt"

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(f.read().splitlines())

def save_seen(seen_ids):
    with open(SEEN_FILE, "w") as f:
        f.write("\n".join(seen_ids))

def is_new(item_id, seen_ids):
    return str(item_id) not in seen_ids