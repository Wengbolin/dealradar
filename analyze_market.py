import sqlite3
import statistics

DB_NAME = "market_data.db"

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

# 创建价格指数表
c.execute("""
CREATE TABLE IF NOT EXISTS model_price_stats (
    model TEXT PRIMARY KEY,
    median_price REAL,
    sample_count INTEGER
)
""")

# 读取数据
c.execute("""
SELECT title, price, first_seen_time, last_seen_time, is_active
FROM listings
""")

rows = c.fetchall()

model_data = {}

for title, price, first, last, active in rows:

    if first is None or last is None:
        continue

    alive_hours = (last - first) / 3600

    if active == 0 and alive_hours <= 24:

        model = title.lower()

        if "iphone 13 pro" in model:
            key = "iphone 13 pro"
        elif "iphone 13" in model:
            key = "iphone 13"
        elif "iphone 14 pro" in model:
            key = "iphone 14 pro"
        elif "iphone 14" in model:
            key = "iphone 14"
        elif "iphone 12 pro" in model:
            key = "iphone 12 pro"
        elif "iphone 12" in model:
            key = "iphone 12"
        else:
            continue

        model_data.setdefault(key, []).append(price)

print("===== 市场价格指数 =====")

for model, prices in model_data.items():

    if not prices:
        continue

    median_price = statistics.median(prices)
    samples = len(prices)

    print(model, median_price, samples)

    c.execute("""
    INSERT OR REPLACE INTO model_price_stats
    (model, median_price, sample_count)
    VALUES (?, ?, ?)
    """, (model, median_price, samples))

conn.commit()
conn.close()
