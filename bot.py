import requests
import time
import subprocess
import sys
import json

TOKEN = "YOUR_BOT_TOKEN"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

last_update_id = None


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
        data={"chat_id": chat_id, "text": text}
    )


def process_query(query, chat_id):
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

    for r in results[:3]:
        msg = f"""🔥 Job Lead

📧 {r['email']}
⭐ {r['score']}

{r['content'][:150]}

🔗 {r['link']}"""

        send_message(chat_id, msg)
        time.sleep(0.5)


while True:
    updates = get_updates()

    for u in updates:
        last_update_id = u["update_id"]

        if "message" in u:
            chat_id = u["message"]["chat"]["id"]
            text = u["message"].get("text", "")

            if text:
                process_query(text, chat_id)

    time.sleep(2)
