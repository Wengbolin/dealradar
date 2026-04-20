import sqlite3
import re
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "market_data.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

MODEL_PATTERNS = {
    "iphone 14 pro": r"iphone\s?14\s?pro",
    "iphone 14": r"iphone\s?14",
    "iphone 13 pro": r"iphone\s?13\s?pro",
    "iphone 13": r"iphone\s?13",
    "iphone 12 pro": r"iphone\s?12\s?pro",
    "iphone 12": r"iphone\s?12"
}

def detect_model(title):

    if not title:
        return None

    t = title.lower()

    for model, pattern in MODEL_PATTERNS.items():
        if re.search(pattern, t):
            return model

    return None


def valid_price(price):

    if price is None:
        return False

    if price < 50:
        return False

    if price > 3000:
        return False

    return True


def is_accessory(title):

    if not title:
        return True

    blacklist = [
        "cover",
        "custodia",
        "case",
        "ricambi",
        "display",
        "vetro",
        "batteria"
    ]

    t = title.lower()

    for w in blacklist:
        if w in t:
            return True

    return False


def process_data():

    logging.info("开始数据处理")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_listings (
        listing_id TEXT PRIMARY KEY,
        title TEXT,
        price REAL,
        model TEXT,
        first_seen_time REAL,
        last_seen_time REAL
    )
    """)

    cursor.execute("""
    SELECT listing_id, title, price, first_seen_time, last_seen_time
    FROM listings
    """)

    rows = cursor.fetchall()

    processed = 0
    skipped = 0

    for row in rows:

        listing_id, title, price, first_seen, last_seen = row

        if not valid_price(price):
            skipped += 1
            continue

        if is_accessory(title):
            skipped += 1
            continue

        model = detect_model(title)

        if not model:
            skipped += 1
            continue

        cursor.execute("""
        INSERT INTO processed_listings
        (listing_id, title, price, model, first_seen_time, last_seen_time)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(listing_id) DO UPDATE SET
            price=excluded.price,
            model=excluded.model,
            last_seen_time=excluded.last_seen_time
        """, (listing_id, title, price, model, first_seen, last_seen))

        processed += 1

    conn.commit()
    conn.close()

    logging.info("处理完成")
    logging.info(f"有效数据: {processed}")
    logging.info(f"过滤数据: {skipped}")


if __name__ == "__main__":
    process_data()
