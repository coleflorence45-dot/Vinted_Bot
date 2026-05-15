# bot_controls.py
import threading
import requests
import time
from datetime import datetime, timedelta
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

pending_messages = {}
last_update_id = 0

def get_keyboard():
    return {
        "inline_keyboard": [[
            {"text": "❤️ Keep", "callback_data": "keep"},
            {"text": "🗑️ Delete", "callback_data": "delete"}
        ]]
    }

def delete_message(message_id):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "message_id": message_id}
    )

def edit_message(message_id, text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageText",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "message_id": message_id,
            "text": text + "\n\n✅ Saved",
            "parse_mode": "Markdown",
            "reply_markup": {"inline_keyboard": []}
        }
    )

def answer_callback(callback_id):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery",
        json={"callback_query_id": callback_id}
    )

def poll_loop():
    global last_update_id
    while True:
        try:
            # Check for button presses
            response = requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
                params={"offset": last_update_id + 1, "timeout": 10},
                timeout=15
            )
            data = response.json()

            for update in data.get("result", []):
                last_update_id = update["update_id"]
                callback = update.get("callback_query")
                if callback:
                    msg_id = callback["message"]["message_id"]
                    text = callback["message"].get("text", "")
                    action = callback["data"]
                    answer_callback(callback["id"])

                    if action == "delete":
                        delete_message(msg_id)
                        pending_messages.pop(msg_id, None)
                        print(f"  🗑️ Message {msg_id} deleted by user")

                    elif action == "keep":
                        edit_message(msg_id, text)
                        pending_messages.pop(msg_id, None)
                        print(f"  ❤️ Message {msg_id} kept by user")

            # Auto-delete messages older than 24 hours
            now = datetime.now()
            for msg_id, info in list(pending_messages.items()):
                if now - info["sent_time"] > timedelta(hours=24):
                    delete_message(msg_id)
                    pending_messages.pop(msg_id, None)
                    print(f"  🗑️ Auto-deleted message {msg_id}")

        except Exception as e:
            print(f"  ⚠️ Poll error: {e}")
            time.sleep(5)

        time.sleep(1)

def start_bot_thread():
    thread = threading.Thread(target=poll_loop, daemon=True)
    thread.start()
    print("✅ Button handler started\n")