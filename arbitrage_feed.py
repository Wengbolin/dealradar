import json
from pathlib import Path
from notifier.telegram import send

CACHE_PATH = Path("arbitrage_cache.json")
PUSHED_PATH = Path("pushed_arbitrage.json")


def load_pushed():

    if not PUSHED_PATH.exists():
        return []

    with open(PUSHED_PATH, "r") as f:
        return json.load(f)


def save_pushed(data):

    with open(PUSHED_PATH, "w") as f:
        json.dump(data, f)


def get_feed(limit=30):

    if not CACHE_PATH.exists():
        return []

    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        deals = json.load(f)

    deals.sort(
        key=lambda x: (x.get("score", 0), x.get("profit", 0)),
        reverse=True
    )

    return deals[:limit]


def push_to_telegram(limit=5):

    deals = get_feed(limit)

    pushed = load_pushed()

    for d in deals:

        deal_id = d["url"]

        if deal_id in pushed:
            continue

        msg = f"""
⚡套利机会

{d['model']}

价格: €{d['price']}
市场价: €{d.get('market_price',0)}

利润: €{d.get('profit',0)}

链接:
{d['url']}
"""

        send(msg)

        pushed.append(deal_id)

    save_pushed(pushed)


if __name__ == "__main__":

    push_to_telegram()
