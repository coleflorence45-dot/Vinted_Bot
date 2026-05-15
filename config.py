# config.py

# --- TELEGRAM ---
TELEGRAM_TOKEN = "your_token_here"
TELEGRAM_CHAT_ID = "your_chat_id_here"

# --- SEARCH KEYWORDS ---
SEARCH_KEYWORDS = [
    "Zara dress",
    "Ted Baker dress",
    "Other Stories dress",
    "Whistles dress",
    "skater dress",
    "prom dress",
    "bridesmaid dress",
    "beach dress",
    "party dress",
    "sheer dress",
    "races dress",
    "special occasion dress",
    "midi dress",
    "maxi dress",
]

# --- PRICE RANGE (£) ---
MIN_PRICE = 10.0
MAX_PRICE = 15.0

# --- CONDITIONS TO ACCEPT (anything not in this list gets skipped) ---
GOOD_CONDITIONS = [
    "new with tags",
    "new without tags",
    "very good",
]

# --- WORDS IN TITLE THAT MEAN SKIP IT ---
BAD_TITLE_KEYWORDS = [
    "stained",
    "damaged",
    "repair",
    "worn",
    "marks",
    "fault",
    "faulty",
    "hole",
    "holes",
]