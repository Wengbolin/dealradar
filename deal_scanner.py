import sqlite3
import time
from pathlib import Path

from profit_filter import extract_model, is_profitable, extract_storage
from score_engine import calculate_score
from decision_engine import make_decision

from api.config import DB_PATH
# =========================
# 加载价格缓存
# =========================

def load_price_cache(cursor):

    cache = {}

    cursor.execute("""
    SELECT model, low_price, median_price
    FROM model_price_stats
    """)

    for model, low_price, median_price in cursor.fetchall():

        key = model.lower()

        cache[key] = {
            "low": low_price,
            "median": median_price
        }

    print("价格缓存加载:", len(cache))

    return cache


# =========================
# 加载流动性缓存
# =========================

def load_velocity_cache(cursor):

    cache = {}

    cursor.execute("""
    SELECT model, velocity_score
    FROM model_velocity_stats
    """)

    for model, velocity in cursor.fetchall():

        cache[model.lower()] = velocity

    print("流动性缓存加载:", len(cache))

    return cache


# =========================
# 套利等级判断
# =========================

def evaluate_deal(price, low_price, median_price):

    if price <= low_price:
        return "🔥 S级套利", median_price - price

    if price <= median_price * 0.85:
        return "⭐ A级套利", median_price - price

    if price <= median_price * 0.9:
        return "B级套利", median_price - price

    if price <= median_price * 0.95:
        return "C级套利", median_price - price

    return None, 0


# =========================
# 发布时间权重
# =========================

def recency_bonus(first_seen_time):

    now = time.time()

    age_minutes = (now - first_seen_time) / 60

    if age_minutes < 10:
        return 20

    if age_minutes < 30:
        return 15

    if age_minutes < 60:
        return 10

    if age_minutes < 120:
        return 5

    return 0


# =========================
# 扫描套利
# =========================

def scan_deals():

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    print("加载价格缓存...")

    price_cache = load_price_cache(cursor)

    velocity_cache = load_velocity_cache(cursor)

    now = time.time()
    recent = now - 3600 * 24

    cursor.execute("""
    SELECT title, price, url, first_seen_time
    FROM listings
    WHERE is_active = 1
    AND first_seen_time >= ?
    """, (recent,))

    rows = cursor.fetchall()

    print("扫描商品:", len(rows))

    deals = []
    seen_urls = set()

    # =========================
    # 🔥 DEBUG 统计（新增）
    # =========================
    debug_counter = {
        "total": 0,
        "duplicate": 0,
        "not_profitable": 0,
        "no_model": 0,
        "bad_keyword": 0,
        "no_price_cache": 0,
        "profit_low": 0,
        "low_velocity": 0,
        "low_score": 0
    }

    # 预加载 eBay 数据（只执行一次）
    cursor.execute("""
    SELECT title, price FROM listings
    WHERE is_active = 1
    AND lower(source) = 'ebay'
    """)

    ebay_rows = cursor.fetchall()
    
    for title, price, url, first_seen_time in rows:

        debug_counter["total"] += 1

        if url in seen_urls:
            debug_counter["duplicate"] += 1
            continue

        seen_urls.add(url)

        try:
            price = float(price)
        except:
            continue

        ok, _, _ = is_profitable(title, "", price)

        if not ok:
            debug_counter["not_profitable"] += 1
            continue

        title_lower = title.lower()

        model_base = extract_model(title)
        storage = extract_storage(title)

        if not model_base:
            debug_counter["no_model"] += 1
            continue

        model_base = model_base.lower()

        if "pro max" in title_lower:
            model = model_base + " pro max"
        elif "pro" in title_lower:
            model = model_base + " pro"
        elif "mini" in title_lower:
            model = model_base + " mini"
        else:
            model = model_base

        BAD_KEYWORDS = [
            "scheda madre", "logic board", "motherboard",
            "chassis", "scocca", "housing", "frame",
            "solo", "per parti", "ricambi", "parts only",
            "broken", "rotto", "non funziona", "guasto"
        ]

        if any(k in title_lower for k in BAD_KEYWORDS):
            debug_counter["bad_keyword"] += 1
            continue

        BAD_SIGNS = [
            "leggere descrizione",
            "non funziona",
            "rotto",
            "da riparare",
            "problema",
            "difetto",
            "guasto"
        ]

        if any(x in title_lower for x in BAD_SIGNS):
            debug_counter["bad_keyword"] += 1
            continue

        BAD_ACCESSORIES = [
            "cover", "custodia", "case",
            "vetro", "glass", "display",
            "batteria", "battery",
            "ricambi", "parts",
            "protezione", "pellicola"
        ]

        if any(x in title_lower for x in BAD_ACCESSORIES):
            debug_counter["bad_keyword"] += 1
            continue

        if not model:
            continue

        model_key = model.lower()

        if storage:
            storage_key = f"{model.lower()} {storage}"
            if storage_key in price_cache:
                model_key = storage_key        

        if "pro" in model_key and storage is not None and storage < 128:
            continue

        if "iphone 12" in model_key and "pro" not in model_key:
            if storage is not None and storage > 256:
                continue

        if model_key not in price_cache:
        
            # 🔥 fallback：去掉 storage 再试一次
            base_key = model_base.lower()

            if base_key in price_cache:
                model_key = base_key
            else:
                debug_counter["no_price_cache"] += 1
                continue

        stats = price_cache[model_key]

        ebay_prices = []

        keywords = model_key.split()

        for t_row, p_row in ebay_rows:
  
            if not p_row:
                continue

            try:
                p = float(p_row)
            except:
                continue

            t_lower = t_row.lower()

            if all(k in t_lower for k in keywords):

                if p < stats["median"] * 0.7:
                    continue

                if p > stats["median"] * 1.3:
                    continue

                ebay_prices.append(p)

        if ebay_prices:

            if len(ebay_prices) < 5:
                ebay_median = stats["median"]
            else:    
                ebay_prices.sort()

                n = len(ebay_prices)

                cutoff = int(n * 0.5)

                ebay_prices = ebay_prices[:cutoff]

                ebay_median = ebay_prices[len(ebay_prices)//2]
               
        else:
            ebay_median = stats["median"]

        if "subito.it" in url:
            source = "SUBITO"
        elif "ebay" in url:
            source = "EBAY"
        else:
            source = "UNKNOWN"

        if source == "SUBITO":
            target_price = ebay_median
        else:
            target_price = stats["median"]

        real_sell_price = target_price * 0.9
        real_sell_price *= 0.85
        real_sell_price -= 15

        profit = real_sell_price - price

        if profit < 5:
            debug_counter["profit_low"] += 1
            continue
        
        velocity = velocity_cache.get(model_key, 0)
        if velocity < 0.01:
            debug_counter["low_velocity"] += 1
            continue

        base_score = calculate_score(
            price,
            target_price,
            velocity,
            first_seen_time
        )

        bonus = recency_bonus(first_seen_time)

        score = base_score + bonus
       
        if storage is None:
            score -= 30

        if score < 10:
            debug_counter["low_score"] += 1
            continue

        level = "🔥 S级套利" if score >= 60 else "⭐ A级套利"

        deal = {
            "title": title,
            "model": model,
            "storage": storage,
            "price": price,
            "market_price": target_price,
            "profit": round(profit, 1),
            "score": round(score, 1),
            "confidence": velocity * 100,
            "level": level,
            "url": url,
            "source": source,
        }

        decision_data = make_decision(deal)

        deal.update(decision_data)

        deals.append(deal)
    # =========================
    # 🔥 DEBUG 输出（新增）
    # =========================
    print("\nDEBUG FILTER STATS:")
    for k, v in debug_counter.items():
        print(k, ":", v)

    return deals


# =========================
# 打印套利
# =========================

def print_deals(deals):

    print("\n🔥 ARBITRAGE OPPORTUNITIES\n")

    if not deals:
        print("没有发现套利机会")
        return

    for d in deals[:10]:

        print(d["level"], "| Score:", round(d["score"], 1))
        print("📱", d["title"])
        print("价格:", d["price"], "€")
        print("预计利润:", round(d["profit"], 1), "€")
        print("-" * 40)


if __name__ == "__main__":
    deals = scan_deals()
    print_deals(deals)
