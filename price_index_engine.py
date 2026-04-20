import sqlite3
import statistics
import time
from pathlib import Path


# =========================
# 数据库路径
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = (BASE_DIR / "data" / "market_data.db").resolve()


# =========================
# 过滤异常价格
# =========================

def remove_outliers(prices):

    if len(prices) < 10:
        return prices

    prices.sort()

    trim = int(len(prices) * 0.2)   # ✅ 修改：10% → 20%

    return prices[trim:-trim]


# =========================
# 计算分位价格
# =========================

def price_percentiles(prices):

    prices.sort()

    n = len(prices)

    low = prices[int(n * 0.25)]
    median = prices[int(n * 0.50)]
    high = prices[int(n * 0.75)]

    return low, median, high


# =========================
# 计算价格指数
# =========================

def compute_price_index():

    print("价格指数引擎启动")

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 创建统计表

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS model_price_stats (

        model TEXT PRIMARY KEY,

        low_price REAL,
        median_price REAL,
        high_price REAL,

        min_price REAL,
        sample_size INTEGER,

        update_time REAL

    )

    """)

    # 读取数据（✅ 修改：只用 eBay）

    cursor.execute("""

    SELECT title, price
    FROM listings
    WHERE lower(source) = 'ebay'
    AND is_active = 1

    """)

    rows = cursor.fetchall()

    model_prices = {}

    from profit_filter import extract_model, extract_storage

    for title, price in rows:

        if not price:
            continue

        model = extract_model(title)
        storage = extract_storage(title)

        if not model:
            continue

        if not storage:
            continue

        # 🔥 构建 storage 维度 key
        if storage:
            key = f"{model.lower()} {storage}"
        else:
            key = model.lower()

        model_prices.setdefault(key, []).append(price)


    print("统计型号数量:", len(model_prices))

    # 计算每个型号价格

    for model, prices in model_prices.items():

        if len(prices) < 10:
            continue

        prices = remove_outliers(prices)

        # =========================
        # 🔥 新增：区间过滤（核心）
        # =========================

        prices.sort()
        median_temp = prices[len(prices)//2]

        filtered = []

        for p in prices:
            if p < median_temp * 0.6:
                continue
            if p > median_temp * 1.4:
                continue
            filtered.append(p)

        if len(filtered) < 3:
            continue

        prices = filtered

        # =========================

        low_price, median_price, high_price = price_percentiles(prices)

        min_price = min(prices)

        sample_size = len(prices)

        cursor.execute("""

        INSERT OR REPLACE INTO model_price_stats
        (model, low_price, median_price, high_price, min_price, sample_size, update_time)

        VALUES (?, ?, ?, ?, ?, ?, ?)

        """, (

            model,
            low_price,
            median_price,
            high_price,
            min_price,
            sample_size,
            time.time()

        ))

        print(
            model,
            "低:", int(low_price),
            "中:", int(median_price),
            "高:", int(high_price),
            "样本:", sample_size
        )

    conn.commit()

    conn.close()

    print("价格指数更新完成")


# =========================

if __name__ == "__main__":

    compute_price_index()
