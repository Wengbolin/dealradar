import sqlite3
import statistics
import re

conn = sqlite3.connect("../data/market_data.db")
cursor = conn.cursor()

cursor.execute("""
SELECT title, price, source
FROM listings
WHERE title LIKE '%iphone%'
""")

rows = cursor.fetchall()

models = {}

for title, price, source in rows:

    title_lower = title.lower()

    # 过滤异常价格
    if price < 50 or price > 2000:
        continue

    # 提取型号
    match = re.search(r'iphone\s\d+\s?(pro max|pro|plus|mini)?', title_lower)

    if not match:
        continue

    model = match.group().strip()

    if model not in models:
        models[model] = {"subito": [], "ebay": []}

    models[model][source].append(price)

print("\n套利检测结果\n")

for model in models:

    subito_prices = models[model]["subito"]
    ebay_prices = models[model]["ebay"]

    if len(subito_prices) < 5 or len(ebay_prices) < 5:
        continue

    subito_median = statistics.median(subito_prices)
    ebay_median = statistics.median(ebay_prices)

    profit = ebay_median - subito_median

    print("型号:", model)
    print(" Subito中位价:", round(subito_median,2))
    print(" eBay中位价 :", round(ebay_median,2))
    print(" 利润:", round(profit,2),"€")

    if profit > 70:
        print(" ★ 强套利机会")

    print()
