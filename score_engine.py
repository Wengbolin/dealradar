# score_engine.py
# 套利评分系统

import time


def calculate_score(price, market_price, velocity, first_seen_time):

    score = 0

    # -----------------
    # 1 价格优势
    # -----------------

    if market_price == 0:
        return 0

    discount = (market_price - price) / market_price

    if discount > 0.55:
        score += 50
    elif discount > 0.40:
        score += 40
    elif discount > 0.30:
        score += 30
    elif discount > 0.20:
        score += 20
    elif discount > 0.10:
        score += 10

    # -----------------
    # 2 流动性（强化版）
    # -----------------

    score += velocity * 30


    # -----------------
    # 3 发布时间
    # -----------------

    age = time.time() - first_seen_time

    if age < 600:
        score += 20
    elif age < 3600:
        score += 10

    return score
