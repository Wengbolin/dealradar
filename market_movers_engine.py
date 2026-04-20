import json
from pathlib import Path
from notifier.telegram import send

CACHE_FILE = Path("arbitrage_cache.json")
SENT_FILE = Path("sent_movers.json")

DROP_THRESHOLD = 100   # 价格下降阈值

def load_sent():

    if not SENT_FILE.exists():
        return set()

    with open(SENT_FILE, "r") as f:
        return set(json.load(f))


def save_sent(sent):

    with open(SENT_FILE, "w") as f:
        json.dump(list(sent), f)

def detect_market_movers():

    if not CACHE_FILE.exists():
        print("没有套利缓存")
        return

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        deals = json.load(f)

    sent = load_sent()

    for d in deals:

        market_price = d.get("market_price", 0)
        price = d.get("price", 0)

        key = f"{d['title']}_{price}"

        if key in sent:
            continue

        if not market_price or not price:
            continue

        drop = market_price - price

        if drop < DROP_THRESHOLD:
            continue

        msg = (
            "📉 MARKET MOVER\n\n"
            f"📱 {d['title']}\n\n"
            f"市场价: {market_price}€\n"
            f"当前价: {price}€\n"
            f"价格下降: -{drop}€\n"
            f"评分: {d.get('score',0)}"
        )

        send(msg)

        sent.add(key)
        save_sent(sent)


if __name__ == "__main__":
    detect_market_movers()
