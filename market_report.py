# market_report.py
# Subito 滚动市场报告（工程优化版）

import sqlite3
import statistics
import time
import json
from pathlib import Path
import requests


# =========================
# 配置
# =========================

BOT_TOKEN = "8513118674:AAEOPPjk20dU2c1tYHqwQmZyi47YvkU9qG0"
CHAT_ID = "8219121142"

MODEL_RULES = {
    "iPhone 14 Pro": ["iphone 14 pro"],
    "iPhone 14": ["iphone 14"],
    "iPhone 13 Pro": ["iphone 13 pro"],
    "iPhone 13": ["iphone 13"],
    "iPhone 12": ["iphone 12"],
}

MODEL_ORDER = [
    "iPhone 12",
    "iPhone 13",
    "iPhone 13 Pro",
    "iPhone 14",
    "iPhone 14 Pro",
]

SHORT_NAME = {
    "iPhone 12": "12",
    "iPhone 13": "13",
    "iPhone 13 Pro": "13P",
    "iPhone 14": "14",
    "iPhone 14 Pro": "14P",
}


# =========================
# Telegram发送
# =========================

def send_telegram(text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": text
        },
        timeout=10
    )


# =========================
# IQR异常过滤
# =========================

def iqr_filter(values):

    if len(values) < 8:
        return values

    q1 = statistics.quantiles(values, n=4)[0]
    q3 = statistics.quantiles(values, n=4)[2]

    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    return [v for v in values if lower <= v <= upper]


# =========================
# 密度窗口过滤
# =========================

def density_window(values):

    if len(values) < 15:
        return values

    values = sorted(values)

    window_size = int(len(values) * 0.6)

    best_span = None
    best_range = None

    for i in range(len(values) - window_size + 1):

        span = values[i + window_size - 1] - values[i]

        if best_span is None or span < best_span:

            best_span = span
            best_range = (values[i], values[i + window_size - 1])

    low, high = best_range

    return [v for v in values if low <= v <= high]


# =========================
# 加权中位数
# =========================

def weighted_median(prices, weights):

    paired = sorted(zip(prices, weights), key=lambda x: x[0])

    total_weight = sum(weights)

    cumulative = 0

    for price, w in paired:

        cumulative += w

        if cumulative >= total_weight / 2:
            return price

    return paired[len(paired)//2][0]


# =========================
# 识别型号
# =========================

def detect_model(title):

    if not title:
        return None

    t = title.lower()

    for model, rules in MODEL_RULES.items():

        for r in rules:

            if r in t:
                return model

    return None


# =========================
# 主函数
# =========================

def main():

    BASE_DIR = Path(__file__).resolve().parents[1]
    DB_PATH = BASE_DIR / "data" / "market_data.db"

    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)

    report_lines = []

    def tg_print(text=""):

        print(text)
        report_lines.append(str(text))

    tg_print("📊 生成滚动市场报告（工程优化版）\n")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # =========================
    # 数据库统计
    # =========================

    c.execute("SELECT COUNT(*) FROM listings")
    total_records = c.fetchone()[0]

    tg_print(f"当前数据库总记录: {total_records}")

    now = time.time()

    # =========================
    # SQL层过滤
    # =========================

    c.execute("""
        SELECT title, price, first_seen_time
        FROM listings
        WHERE price BETWEEN 50 AND 2000
        AND title LIKE '%iphone%'
        AND first_seen_time >= ?
    """, (now - 86400 * 7,))

    rows = c.fetchall()

    model_prices = {}

    for title, price, ts in rows:

        model = detect_model(title)

        if not model:
            continue

        model_prices.setdefault(model, []).append((price, ts))

    results = []

    for model in MODEL_ORDER:

        if model not in model_prices:
            continue

        data = model_prices[model]

        if len(data) < 20:
            continue

        prices = [p for p, _ in data]

        filtered = iqr_filter(prices)
        filtered = density_window(filtered)

        if len(filtered) < 10:
            continue

        weighted_prices = []
        weights = []

        for price, ts in data:

            if price not in filtered:
                continue

            age_hours = (now - ts) / 3600

            weight = 1 / (1 + age_hours)

            weighted_prices.append(price)
            weights.append(weight)

        median_price = weighted_median(weighted_prices, weights)

        results.append({
            "model": model,
            "count": len(weighted_prices),
            "median": round(median_price, 2),
            "min": min(weighted_prices),
            "max": max(weighted_prices),
        })

    # =========================
    # 输出报告
    # =========================

    tg_print("\n📊 滚动市场报告")
    tg_print("型号  样本  最低  中位  最高  空间")
    tg_print("--------------------------------")

    price_db = {}

    for r in results:

        name = SHORT_NAME.get(r["model"], r["model"])

        edge = int((r["median"] - r["min"]) / r["median"] * 100)

        line = (
            f"{name:<4}"
            f"{r['count']:<6}"
            f"{int(r['min']):<6}"
            f"{int(r['median']):<6}"
            f"{int(r['max']):<6}"
            f"🔥{edge:>2}%"
        )

        tg_print(line)

        # ⭐ 自动生成价格数据库
        median = r["median"]

        price_db[r["model"]] = {
            "128": round(median * 0.9),
            "256": round(median * 0.95),
            "512": round(median * 1.05)
        }

    conn.close()

    # =========================
    # 写入 prices.json
    # =========================

    prices_path = BASE_DIR / "data" / "prices.json"

    with open(prices_path, "w") as f:
        json.dump(price_db, f, indent=2)

    print("\n✅ prices.json 已更新（市场自动定价）")

    report_text = "\n".join(report_lines)

    send_telegram(report_text)


if __name__ == "__main__":
    main()
