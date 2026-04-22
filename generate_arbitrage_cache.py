import json
from pathlib import Path

from api.config import DB_PATH   # 👈 加这一行

from deal_scanner import scan_deals
from notifier.telegram import send

CACHE_FILE = Path("arbitrage_cache.json")
SENT_FILE = Path("sent_arbitrage.json")


def load_sent():
    if not SENT_FILE.exists():
        return set()
    with open(SENT_FILE, "r") as f:
        return set(json.load(f))


def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent), f)


def classify(deals):
    """分级系统🔥"""

    for d in deals:

        profit = d.get("profit", 0)

        if profit >= 80:
            d["level"] = "A级"
        elif profit >= 40:
            d["level"] = "B级"
        else:
            d["level"] = "C级"

    return deals


def expand_deals(deals):
    """保证至少10条🔥"""

    if not deals:
        return []

    expanded = deals.copy()

    while len(expanded) < 10:
        expanded += deals

    return expanded[:10]


def generate_cache():

    print("开始生成套利缓存...")

    deals = scan_deals()
    # 👉 去重（按URL）
    seen = set()
    unique_deals = []

    for d in deals:
        key = d.get("url")

        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)
        unique_deals.append(d)

    deals = unique_deals

    if deals is None:
        deals = []

    # 👉 排序
    deals.sort(key=lambda x: x.get("profit", 0), reverse=True)

    # 👉 分级
    deals = classify(deals)

    # 👉 保底扩展🔥
    #deals = expand_deals(deals)

    # 👉 写入缓存
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(deals, f, ensure_ascii=False, indent=2)

    print("缓存生成完成")
    print("套利机会:", len(deals))

    # =====================
    # Telegram推送（只推A级）
    # =====================

    sent = load_sent()

    for d in deals:

        if d.get("level") != "A级":
            continue

        key = f"{d['title']}_{d['price']}"

        if key in sent:
            continue

        msg = (
            "🔥 A级套利机会\n\n"
            f"📱 {d['title']}\n\n"
            f"价格: {d['price']}€\n"
            f"市场价: {d.get('market_price',0)}€\n"
            f"利润: {d.get('profit',0)}€\n"
        )

        send(msg)

        sent.add(key)

    save_sent(sent)


if __name__ == "__main__":
    generate_cache()

