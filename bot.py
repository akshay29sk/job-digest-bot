# =====================================
# LinkedIn Hiring Radar Bot
# Version: v1.0.0-bot
# =====================================

import requests
import time
import subprocess
import sys
import json

TOKEN = "YOUR_BOT_TOKEN"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

last_update_id = None


# ==============================
# TELEGRAM API
# ==============================
def get_updates():
    global last_update_id

    url = BASE_URL + "/getUpdates"

    if last_update_id:
        url += f"?offset={last_update_id + 1}"

    res = requests.get(url).json()
    return res.get("result", [])


def send_message(chat_id, text):
    requests.post(
        BASE_URL + "/sendMessage",
        data={
            "chat_id": chat_id,
            "text": text
        }
    )


# ==============================
# CORE LOGIC
# ==============================
def run_search(query, chat_id):
    result = subprocess.run(
        [
            sys.executable,
            "main.py",
            query,
            "24h",
            "prefer_email",
            "5",
            "global",
            "", ""
        ],
        capture_output=True,
        text=True
    )

    try:
        results = json.loads(result.stdout.strip())
    except:
        send_message(chat_id, "❌ Failed to fetch results")
        return

    if not results:
        send_message(chat_id, "⚠️ No jobs found")
        return

    send_message(chat_id, f"🔎 Results for: {query}")

    for r in results[:3]:
        msg = f"""🔥 Job Lead

📧 {r['email']}
⭐ {r['score']}

{r['content'][:150]}

🔗 {r['link']}"""

        send_message(chat_id, msg)
        time.sleep(0.4)


# ==============================
# MESSAGE HANDLER
# ==============================
def handle_message(text, chat_id):

    text = text.lower().strip()

    # Help
    if text in ["/start", "/help"]:
        send_message(chat_id,
        """🤖 LinkedIn Hiring Radar Bot

Usage:
/search product owner
/search business analyst pune

Just type your role and I’ll fetch jobs 🔍"""
        )
        return

    # Command mode
    if text.startswith("/search"):
        query = text.replace("/search", "").strip()

        if not query:
            send_message(chat_id, "❗ Please provide a role. Example:\n/search product owner")
            return

        run_search(query, chat_id)
        return

    # Free text mode (auto search)
    run_search(text, chat_id)


# ==============================
# LOOP
# ==============================
print("🤖 Bot started...")

while True:
    updates = get_updates()

    for u in updates:
        last_update_id = u["update_id"]

        if "message" in u:
            chat_id = u["message"]["chat"]["id"]
            text = u["message"].get("text", "")

            if text:
                handle_message(text, chat_id)

    time.sleep(2)
