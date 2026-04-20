import sqlite3
import statistics
import json
import time

DB_PATH = "../data/market_data.db"


def load_prices(model):

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 只读取最近7天
    seven_days = time.time() - 604800

    cur.execute("""
    SELECT price, first_seen_time
    FROM processed_listings
    WHERE price IS NOT NULL
    AND model LIKE ?
    AND first_seen_time > ?
    """, ("%"+model+"%", seven_days))

    rows = cur.fetchall()
    conn.close()

    data = []

    for price, ts in rows:

        if ts is None:
            continue

        # 过滤异常价格
        if price < 200:
            continue

        if price > 800:
            continue

        data.append((ts, price))

    return data


def build_trend(data, bucket_size):

    buckets = {}

    for ts, price in data:

        bucket = int(ts // bucket_size) * bucket_size

        if bucket not in buckets:
            buckets[bucket] = []

        buckets[bucket].append(price)

    trend = []

    for bucket in sorted(buckets.keys()):

        prices = buckets[bucket]

        if len(prices) < 3:
            continue

        median_price = statistics.median(prices)

        trend.append([bucket, median_price])

    # -------- moving average 平滑 --------

    smoothed = []

    for i in range(len(trend)):

        if i == 0 or i == len(trend) - 1:
            smoothed.append(trend[i])
            continue

        avg = (
            trend[i-1][1] +
            trend[i][1] +
            trend[i+1][1]
        ) / 3

        smoothed.append([trend[i][0], avg])

    return smoothed


# -------- 新增：自动识别所有 iPhone 型号 --------

def get_models():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    SELECT DISTINCT model
    FROM processed_listings
    WHERE model LIKE 'iphone%'
    """)

    rows = cur.fetchall()
    conn.close()

    models = [r[0] for r in rows]

    return models


if __name__ == "__main__":

    models = get_models()

    print("Detected models:", len(models))

    cache = {}

    for model in models:

        prices = load_prices(model)

        print(model, "records:", len(prices))

        trend = build_trend(prices, 21600)

        cache[model] = trend

    with open("trend_cache.json", "w") as f:
        json.dump(cache, f)

    print("Trend cache generated")
