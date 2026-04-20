# market_radar_engine.py
# Market Radar Engine

import sqlite3


DB_PATH = "../data/market_data.db"


def get_hot_models(limit=10):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT model, COUNT(*) as listings
    FROM processed_listings
    WHERE model IS NOT NULL
    GROUP BY model
    ORDER BY listings DESC
    LIMIT ?
    """

    cursor.execute(query,(limit,))
    rows = cursor.fetchall()

    conn.close()

    results = []

    for row in rows:
        results.append({
            "model": row[0],
            "listings": row[1]
        })

    return results

def get_arbitrage_index(limit=10):
    """
    套利指数：低于市场平均价最多的型号
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT 
        model,
        AVG(price) as avg_price,
        MIN(price) as min_price
    FROM processed_listings
    WHERE model IS NOT NULL
    GROUP BY model
    HAVING COUNT(*) > 2
    ORDER BY (avg_price - min_price) DESC
    LIMIT ?
    """

    cursor.execute(query, (limit,))
    rows = cursor.fetchall()

    conn.close()

    results = []

    for row in rows:

        model = row[0]
        avg_price = row[1]
        min_price = row[2]

        profit = avg_price - min_price

        results.append({
            "model": model,
            "profit": round(profit,2)
        })

    return results

def get_velocity_index(limit=10):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT 
        model,
        AVG(last_seen_time - first_seen_time) as lifetime
    FROM processed_listings
    WHERE model IS NOT NULL
    GROUP BY model
    HAVING COUNT(*) > 5
    ORDER BY lifetime ASC
    LIMIT ?
    """

    cursor.execute(query,(limit,))
    rows = cursor.fetchall()

    conn.close()

    results = []

    for row in rows:

        model = row[0]
        lifetime = row[1]

        results.append({
            "model": model,
            "lifetime": round(lifetime/3600,2)  # 转换为小时
        })

    return results
