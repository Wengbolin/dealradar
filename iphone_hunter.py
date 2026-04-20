import time
import re
import os
import sqlite3
import statistics
from pathlib import Path

import requests

from market_collector import update_listing, cleanup_old_records
from crawler.subito_crawler import fetch_ads
from crawler.ebay_crawler import fetch_ebay


# ======================
# 数据库路径
# ======================

BASE_DIR = Path(__file__).resolve().parent
from config import DB_PATH

print("Hunter 启动 - Subito + eBay")


# ======================
# 型号识别
# ======================

def detect_model(title):

    t = (title or "").lower()

    if "iphone 14 pro" in t: return "iPhone 14 Pro"
    if "iphone 14" in t: return "iPhone 14"
    if "iphone 13 pro" in t: return "iPhone 13 Pro"
    if "iphone 13" in t: return "iPhone 13"
    if "iphone 12 pro" in t: return "iPhone 12 Pro"
    if "iphone 12" in t: return "iPhone 12"

    return None


# ======================
# 计算市场中位价
# ======================

def get_model_medians():

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    c.execute("SELECT title,price FROM listings")

    rows = c.fetchall()

    conn.close()

    mp = {}

    for title,price in rows:

        model = detect_model(title)

        if model:
            mp.setdefault(model,[]).append(price)

    medians = {}

    for m,prices in mp.items():

        if len(prices) < 30:
            continue

        prices.sort()

        trim = int(len(prices)*0.1)

        prices = prices[trim:-trim]

        medians[m] = statistics.median(prices)

    return medians


# ======================
# 套利评分（保留但不使用）
# ======================

def execution_score(price,median):

    ratio = price/median if median else 999

    if ratio <= 0.75: return 30
    if ratio <= 0.8: return 25
    if ratio <= 0.85: return 20
    if ratio <= 0.9: return 10

    return 0


# ======================
# 单次执行（已移除循环）
# ======================
try:

    print(">>> 抓取 Subito")

    subito_raw = fetch_ads()

    subito_ads = []

    for ad in subito_raw:

        price = None

        try:

            for f in ad.get("features",[]):

                if f.get("label") == "Prezzo":

                    price = int(re.sub(r"\D","",f["values"][0]["value"]))

        except:
            pass
 
        subito_ads.append({
            "title": ad.get("subject",""),
            "url": ad["urls"]["default"],
            "price": price,
            "source": "subito"
        })

    print(">>> 抓取 eBay")

    ebay_ads = fetch_ebay()

    all_ads = subito_ads + ebay_ads


    print(">>> 写入数据库")

    for ad in all_ads:

        if not ad["price"]:
            continue

        url = ad["url"]

        update_listing(
            url,
            ad["title"],
            ad["price"],
            ad["source"],
            url
        )

    cleanup_old_records()

    print("✅ Hunter 完成")


except Exception as e:

    print("ERROR:", e)
