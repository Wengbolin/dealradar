import sqlite3
import time
import re
from profit_filter import extract_storage
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "market_data.db"


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


def compute_velocity():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = time.time()
    day_ago = now - 86400

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS model_velocity_stats (

        model TEXT PRIMARY KEY,

        stock INTEGER,
        new_count INTEGER,
        sold_count INTEGER,

        velocity_score REAL,
        speed_level TEXT,

        update_time REAL
    )
    """)

    cursor.execute("""
    SELECT title, first_seen_time, last_seen_time, is_active
    FROM listings
    """)

    rows = cursor.fetchall()

    inventory = {}
    new_counts = {}
    sold_counts = {}

    for title, first_seen, last_seen, active in rows:

        model = detect_model(title)
        storage = extract_storage(title)

        if not model:
            continue

        # 🔥 构建 storage key
        if storage:
            key = f"{model} {storage}"
        else:
            continue

        inventory[key] = inventory.get(key, 0) + 1

        if first_seen > day_ago:
            new_counts[key] = new_counts.get(key, 0) + 1

        if active == 0 and last_seen > day_ago:
            sold_counts[key] = sold_counts.get(key, 0) + 1

    print("===== 市场流动性 (24h) =====\n")

    models = set(inventory.keys())

    for m in sorted(models):

        stock = inventory.get(m, 0)
        new = new_counts.get(m, 0)
        sold = sold_counts.get(m, 0)

        # 🔥 双因子模型
        if stock == 0:
            velocity = 0
        else:
            supply_pressure = new / stock
            sell_signal = sold / stock if stock > 0 else 0
            velocity = supply_pressure * 0.7 + sell_signal * 0.3

        if velocity > 0.08:
            speed = "FAST"
            score = 1.0

        elif velocity > 0.03:
            speed = "NORMAL"
            score = 0.6

        else:
            speed = "SLOW"
            score = 0.2

        print(f"{m:15} 库存:{stock:3} 新增:{new:3} 消失:{sold:3} 流动性:{speed}")

        # ✅ 正确写入数据库（修复）
        cursor.execute("""
        INSERT OR REPLACE INTO model_velocity_stats
        (model, stock, new_count, sold_count, velocity_score, speed_level, update_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            m,
            stock,
            new,
            sold,
            score,
            speed,
            time.time()
        ))

    # ======================
    # 🔥 容量偏好（正确位置：循环外）
    # ======================

    print("\n===== 容量偏好 =====\n")

    model_groups = {}

    for m in models:
        base = " ".join(m.split()[:2])
        model_groups.setdefault(base, []).append(m)

    for base, variants in model_groups.items():

        if len(variants) < 2:
            continue

        print(f"\n{base}:")

        ranked = []

        for v in variants:
            stock = inventory.get(v, 0)
            new = new_counts.get(v, 0)

            if stock == 0:
                continue

            score = new / stock
            ranked.append((v, score))

        ranked.sort(key=lambda x: x[1], reverse=True)

        for v, s in ranked:
            print(f"  {v:20} 吸收率: {round(s,4)}")

    conn.commit()
    conn.close()

    print("\n流动性指数更新完成")


if __name__ == "__main__":
    compute_velocity()
