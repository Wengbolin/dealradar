import sqlite3
import time
from pathlib import Path

from api.config import DB_PATH

DB_NAME = DB_PATH

def init_db():

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS listings (
        listing_id TEXT PRIMARY KEY,
        title TEXT,
        price REAL,
        source TEXT,
        first_seen_time REAL,
        last_seen_time REAL,
        is_active INTEGER,
        url TEXT
    )
    """)

    c.execute("PRAGMA table_info(listings)")
    columns = [row[1] for row in c.fetchall()]

    if "source" not in columns:
        print(">>> 升级数据库: 添加 source 字段")
        c.execute("ALTER TABLE listings ADD COLUMN source TEXT")

    if "url" not in columns:
        print(">>> 升级数据库: 添加 url 字段")
        c.execute("ALTER TABLE listings ADD COLUMN url TEXT")

    if "image_url" not in columns:
        print(">>> 升级数据库: 添加 image_url 字段")
        c.execute("ALTER TABLE listings ADD COLUMN image_url TEXT")

    conn.commit()
    conn.close()


# 关键修改：url 默认 None
def update_listing(listing_id, title, price, source, url=None, image_url=None):

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    now = time.time()

    c.execute(
        "SELECT listing_id FROM listings WHERE listing_id=?",
        (listing_id,)
    )

    result = c.fetchone()

    if result:

        c.execute("""
        UPDATE listings
        SET title=?,
            price=?,
            source=?,
            url=?,
            image_url=?,
            last_seen_time=?,
            is_active=1
        WHERE listing_id=?
        """, (title, price, source, url, image_url, now, listing_id))
        
    else:

        c.execute("""
        INSERT INTO listings
        (listing_id, title, price, source, url,image_url, first_seen_time, last_seen_time, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (listing_id, title, price, source, url, image_url,  now, now))

    conn.commit()
    conn.close()


def mark_inactive():

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    cutoff = time.time() - 86400

    c.execute("""
    UPDATE listings
    SET is_active = 0
    WHERE last_seen_time < ?
    """, (cutoff,))
    print("UPDATED records")

    conn.commit()
    conn.close()


def cleanup_old_records():

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    cutoff = time.time() - (86400 * 7)

    c.execute("""
    DELETE FROM listings
    WHERE is_active = 0
    AND last_seen_time < ?
    """, (cutoff,))

    conn.commit()
    conn.close()


