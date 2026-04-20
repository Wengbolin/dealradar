import sqlite3
import json
from pathlib import Path

DB_PATH = Path("../data/market_data.db")

def get_top_arbitrage(limit=20):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        title,
        model,
        price,
        listing_id
    FROM processed_listings
    ORDER BY price ASC
    LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    results = []
    for r in rows:
        results.append(dict(r))

    conn.close()

    return results


if __name__ == "__main__":

    data = get_top_arbitrage()

    print(json.dumps(data, indent=2))

