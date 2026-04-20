import requests
import os

BOT_TOKEN = os.getenv("TG_BOT_TOKEN","").strip()
CHAT_ID = os.getenv("TG_CHAT_ID","").strip()

def send(msg):

    if not BOT_TOKEN or not CHAT_ID:
        print("TG SKIP")
        return False

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )

        return r.status_code == 200

    except Exception as e:
        print("TG ERROR:", e)
        return False
