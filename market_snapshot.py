import sqlite3
import statistics

DB_PATH = "../data/market_data.db"

def detect_model(title):

    t = (title or "").lower()

    if "iphone 14 pro" in t:
        return "iPhone 14 Pro"

    if "iphone 14" in t:
        return "iPhone 14"

    if "iphone 13 pro" in t:
        return "iPhone 13 Pro"

    if "iphone 13" in t:
        return "iPhone 13"

    if "iphone 12" in t:
        return "iPhone 12"

    return None


def snapshot():

    conn = sqlite3.connect(DB_PATH)

    c = conn.cursor()

    c.execute("SELECT title, price FROM listings")

    rows = c.fetchall()

    conn.close()

    data = {}

    for title, price in rows:

        model = detect_model(title)

        if not model:
            continue

        data.setdefault(model, []).append(price)

    print("\n===== 市场快照 =====\n")

    for model, prices in data.items():

        if len(prices) < 30:
            continue

        prices.sort()

        trim = int(len(prices) * 0.1)

        prices = prices[trim:-trim]

        median = statistics.median(prices)

        low = min(prices)

        high = max(prices)

        print(model)
        print("样本:", len(prices))
        print("中位价:", int(median), "€")
        print("最低价:", low, "€")
        print("最高价:", high, "€")
        print("")


if __name__ == "__main__":

    snapshot()
