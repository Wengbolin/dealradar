from api.auth import create_access_token, verify_token
print("SERVER FILE LOADED:", __file__)
from fastapi import FastAPI, Header, Depends, Request
import json
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3
import bcrypt
import stripe
import math
from pathlib import Path
from datetime import datetime, timedelta

from api.config import STRIPE_SECRET_KEY
from api.stripe_webhook import router as stripe_webhook_router
from api.routes.pages import router as pages_router

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from market_radar_engine import get_hot_models, get_arbitrage_index, get_velocity_index

from market_collector import init_db

stripe.api_key = STRIPE_SECRET_KEY

import os

app = FastAPI(title="欧洲二手市场情报API")

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(stripe_webhook_router)
app.include_router(pages_router)

# =========================
# 路径配置
# =========================
from api.config import DB_PATH
from pathlib import Path

CACHE_PATH = Path(__file__).resolve().parent.parent / "arbitrage_cache.json"

if os.path.exists("templates"):
    templates = Jinja2Templates(directory="templates")
else:
    templates = None

# =========================
# 工具函数
# =========================

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def get_current_user(authorization: str = Header(None)):

    if not authorization:
        return None

    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)

    if not payload:
        return None

    user_id = payload.get("user_id")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, membership_level, stripe_customer_id
        FROM users WHERE id=?
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "user_id": row["id"],
        "username": row["username"],
        "plan": row["membership_level"],
        "customer_id": row["stripe_customer_id"]
    }


def load_arbitrage_cache():
    print("📦 LOAD CACHE CALLED:", CACHE_PATH)

    if not CACHE_PATH.exists():
        print("❌ CACHE NOT FOUND")
        return []

    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("❌ CACHE ERROR:", e)
        return []


def calculate_market_data():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT model, price
        FROM processed_listings
        WHERE price IS NOT NULL
        AND price BETWEEN 50 AND 2000
    """)

    rows = cursor.fetchall()
    conn.close()

    from collections import defaultdict
    data = defaultdict(list)

    for r in rows:
        model = r["model"]
        price = r["price"]

        if model:
            data[model].append(price)

    result = []

    for model, prices in data.items():
        if len(prices) < 10:   # 👉 你现在数据少，先放宽
            continue

        prices.sort()
        n = len(prices)

        median = prices[n//2]
        low = prices[int(n*0.25)]
        high = prices[int(n*0.75)]

        # 流动性
        if n > 200:
            liquidity = "Very High"
        elif n > 100:
            liquidity = "High"
        elif n > 50:
            liquidity = "Medium"
        else:
            liquidity = "Low"

        result.append({
            "model": model,
            "price": round(median, 2),
            "low": round(low, 2),
            "high": round(high, 2),
            "liquidity": liquidity,
            "count": n
        })

    result.sort(key=lambda x: x["count"], reverse=True)

    return result[:6]

def build_market_lookup(market_data):
    lookup = {}
    for m in market_data:
        lookup[m["model"].lower()] = m
    return lookup

# =========================
# 首页 API
# =========================
@app.get("/api/home")
def homepage():
    print("🔥 HOMEPAGE CALLED")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM listings")
    total_listings = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM listings WHERE is_active = 1")
    active_listings = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT model) FROM processed_listings")
    models = cursor.fetchone()[0]

    conn.close()

    deals = load_arbitrage_cache()
    deals.sort(key=lambda x: x["profit"], reverse=True)

    # 原始排序
    deals = load_arbitrage_cache()
    deals.sort(key=lambda x: x.get("profit", 0), reverse=True)

    # 高质量机会（原逻辑）
    top_deals = [d for d in deals if d.get("profit", 0) > 30][:5]

    # 👉 fallback（关键🔥）
    if not top_deals:
        top_deals = deals[:5]  # 强制给前5个（哪怕利润低）

    market = calculate_market_data()

    market_lookup = build_market_lookup(market)

    for d in deals:
        # ✅ 删除旧评分
        d.pop("score", None)
        d.pop("level", None)
        d.pop("decision", None)
    
        model = d.get("model", "").lower()

        if model in market_lookup:
            market_price = market_lookup[model]["price"]
            d["market_price"] = market_price

            buy_price = d.get("price", 0)

            # ✅ 重新计算利润（核心）
            d["profit"] = round(market_price - buy_price, 2)
            d["roi"] = round((d["profit"] / buy_price) * 100, 1) if buy_price else 0
            
            # ✅ 新评分系统
            if d["roi"] >= 60 and d["profit"] >= 80:
                d["level"] = "S"
                d["decision"] = "BUY"
            elif d["roi"] >= 40:
                d["level"] = "A"
                d["decision"] = "BUY"
            elif d["roi"] >= 20:
                d["level"] = "B"
                d["decision"] = "WATCH"
            else:
                d["level"] = "C"
                d["decision"] = "SKIP"            

            # 👉 新增这里
            if d["level"] == "S":
                d["tag"] = "🔥 Hot Deal"
            elif d["level"] == "A":
                d["tag"] = "⭐ Best Pick"
            elif d["level"] == "B":
                d["tag"] = "👀 Watch"
            else:
                d["tag"] = "❌ Skip"

            # 👉 新增
            if d["decision"] == "BUY":
                d["action_text"] = "Buy now"
            elif d["decision"] == "WATCH":
                d["action_text"] = "Monitor price"
            else:
                d["action_text"] = "Skip this deal"

    top_deals.sort(
        key=lambda x: (x.get("profit", 0), x.get("roi", 0)),
        reverse=True
    )
     
    for d in top_deals:

        # ✅ 保证 roi 存在（核心防炸）
        if "roi" not in d:
            buy_price = d.get("price", 0)
            market_price = d.get("market_price", buy_price)

            profit = market_price - buy_price
            d["profit"] = round(profit, 2)
            d["roi"] = round((profit / buy_price) * 100, 1) if buy_price else 0

        # ✅ 再用 roi 计算
        roi = d.get("roi", 0)

        d["score"] = round(roi * 1.2, 1)
        d["confidence"] = min(100, round(roi * 0.8, 1))

        d.pop("invest_eur", None)

    return {
        "stats":{
            "total_listings": total_listings,
            "active_listings": active_listings,
            "models": models,
            "arbitrage": len(deals)
        },

        "top_deals": top_deals,
        "all_deals": deals,   # 👈 新增
        "market": market
    }

@app.get("/api/account")
def get_account(user=Depends(get_current_user)):

    if not user:
        return {"status": "error", "message": "not authenticated"}

    user_id = user["user_id"]
    plan = user["plan"]

    deals = load_arbitrage_cache()

    # 今日总机会（简单版）
    today_profit = sum(d.get("profit", 0) for d in deals[:10])

    # 权限限制
    limit = 2
    if plan == 1:
        limit = 10
    elif plan >= 2:
        limit = 999

    missed_profit = sum(
        d.get("profit", 0)
        for i, d in enumerate(deals)
        if i >= limit
    )

    deals_today = min(limit, len(deals))

    return {
        "username": user["username"],
        "customer_id": user["customer_id"] or "-",

        "today_profit": round(today_profit, 2),
        "missed_profit": round(missed_profit, 2),

        "deals_today": deals_today,
        "api_requests": 0,
        "plan": plan   # ✅ 必须加这个
    }

# =========================
# Radar API
# =========================

@app.get("/api/radar/hot_models")
def radar_hot_models(user=Depends(get_current_user)):

    if not user:
        return {"status": "error", "message": "not authenticated"}

    user_id = user["user_id"]

    if not check_permission(user_id, "view_radar"):
        return {"status": "error", "message": "no permission"}

    return get_hot_models()

@app.get("/api/radar/arbitrage_index")
def radar_arbitrage_index(user=Depends(get_current_user)):

    if not user:
        return {"status": "error", "message": "not authenticated"}

    user_id = user["user_id"]

    if not check_permission(user_id, "view_arbitrage"):
        return {"status": "error", "message": "no permission"}

    return get_arbitrage_index()


@app.get("/api/radar/velocity")
def radar_velocity(user_id: int = Depends(get_current_user)):

    if not user_id:
        return {"status": "error", "message": "not authenticated"}

    if not check_permission(user_id, "view_velocity"):
        return {"status": "error", "message": "no permission"}

    return get_velocity_index()

@app.on_event("startup")
def startup_event():
    init_db()

# =========================
# Price Trend
# =========================
from time import time

@app.get("/api/price_trend")
def price_trend(model: str, period: str = "24H"):

    conn = get_db()
    cursor = conn.cursor()

    seconds = {
        "1H": 3600,
        "24H": 86400,
        "7D": 604800,
        "30D": 2592000,
        "1Y": 31536000
    }.get(period.upper(), 2592000)

    now = int(time())
    start_time = now - seconds

    cursor.execute("""
        SELECT price, first_seen_time
        FROM listings
        WHERE title LIKE ?
        AND first_seen_time > ?
        ORDER BY first_seen_time DESC
        LIMIT 200
    """, ("%"+model+"%", start_time))

    rows = cursor.fetchall()
    rows.reverse()

    result = []

    for r in rows:
        result.append({
            "price": r[0],
            "time": int(r[1])
        })

    return result

# =========================
# Market Stats
# =========================

@app.get("/api/market_stats")
def market_stats(user_id: int = Depends(get_current_user)):

    if not user_id:
        return {"status": "error", "message": "not authenticated"}

    if not check_permission(user_id, "view_statistics"):
        return {"status": "error", "message": "no permission"}

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM listings")
    total_listings = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM listings WHERE is_active = 1")
    active_listings = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT model) FROM processed_listings")
    model_count = cursor.fetchone()[0]

    conn.close()

    deals = load_arbitrage_cache()

    return {
        "total_listings": total_listings,
        "active_listings": active_listings,
        "models": model_count,
        "arbitrage_opportunities": len(deals)
    }

# =========================
# Arbitrage API
# =========================

@app.get("/api/arbitrage")
def get_arbitrage(profit: int = 0, user=Depends(get_current_user)):

    if not user:
        return {"status": "error", "message": "not authenticated"}

    plan = user["plan"]

    deals = load_arbitrage_cache()
    filtered = [d for d in deals if d.get("profit", 0) >= profit]

    # 🥉 Free
    if plan == 0:
        return filtered[:1]

    # 🥈 Starter
    elif plan == 1:
        return filtered[:10]

    # 🥇 Pro
    else:
        return filtered[:20]


@app.get("/api/top_arbitrage")
def top_arbitrage(user_id: int = Depends(get_current_user)):

    if not user_id:
        return {"status": "error", "message": "not authenticated"}

    if not check_permission(user_id, "view_arbitrage"):
        return {"status": "error", "message": "no permission"}

    deals = load_arbitrage_cache()
    deals.sort(key=lambda x: x["profit"], reverse=True)

    return deals[:10]


@app.get("/api/new_arbitrage")
def new_arbitrage(user_id: int = Depends(get_current_user)):

    if not user_id:
        return {"status": "error", "message": "not authenticated"}

    if not check_permission(user_id, "view_arbitrage"):
        return {"status": "error", "message": "no permission"}

    deals = load_arbitrage_cache()
    deals.sort(key=lambda x: x.get("score", 0), reverse=True)

    return deals[:5]

# =========================
# 用户系统
# =========================

class UserRegister(BaseModel):
    username: str
    email: str
    password: str


@app.post("/api/register")
def register(user: UserRegister):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:

        trial_end = datetime.utcnow() + timedelta(days=14)

        password_hash = bcrypt.hashpw(
            user.password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute(
            """
            INSERT INTO users
            (username,email,password_hash,membership_level,trial_end,created_at)
            VALUES (?,?,?,?,?,?)
            """,
            (
                user.username,
                user.email,
                password_hash,
                0,
                trial_end,
                datetime.utcnow()
            )
        )

        conn.commit()

        return {"status": "ok"}

    except Exception as e:

        return {"status": "error", "message": str(e)}


class UserLogin(BaseModel):
    username: str
    password: str


@app.post("/api/login")
def login(user: UserLogin):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id,password_hash,membership_level FROM users WHERE username=?",
        (user.username,)
    )

    result = cursor.fetchone()

    if not result:
        return {"status": "error", "message": "invalid credentials"}

    user_id = result[0]
    password_hash = result[1]
    membership_level = result[2] if len(result) > 2 else 1

    if membership_level is None:
        membership_level = 1

    if bcrypt.checkpw(
        user.password.encode("utf-8"),
        password_hash.encode("utf-8")
    ):
        from api.auth import create_access_token

        token = create_access_token(user_id, membership_level)

        return {
            "access_token": token,
            "token_type": "bearer"
        }

# =========================
# Stripe Checkout
# =========================
@app.post("/api/create_checkout_session")
def create_checkout_session(
    data: dict,
    user=Depends(get_current_user)
):

    if not user:
        return {"error": "not authenticated"}

    plan = data.get("plan")

    # ✅ 定价逻辑
    if plan == "starter":
        price = 990
        plan_level = 1
        name = "DealRadar Starter"

    elif plan == "pro":
        price = 1990
        plan_level = 2
        name = "DealRadar Pro"

    else:
        return {"error": "invalid plan"}

    session = stripe.checkout.Session.create(
        customer_email=(str(user["user_id"]) + "@test.com"),
        metadata={
            "user_id": str(user["user_id"]),
            "plan": str(plan_level)
        },
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{
            "price_data":{
                "currency":"eur",
                "product_data":{
                    "name": name
                },
                "unit_amount": price,
                "recurring":{
                    "interval":"month"
                }
            },
            "quantity":1
        }],
        success_url="http://127.0.0.1:8000/success",
        cancel_url="http://127.0.0.1:8000/cancel"
    )

    return {"url": session.url}

@app.post("/api/create_portal_session")
def create_portal_session(user=Depends(get_current_user)):

    if not user:
        return {"error": "not authenticated"}

    customer_id = user.get("customer_id")

    if not customer_id:
        return {"error": "no subscription"}

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url="http://127.0.0.1:8000/account"
    )

    return {"url": session.url}


# =========================
# Cancel Subscription
# =========================

@app.post("/api/cancel_subscription")
def cancel_subscription(user_id: int = Depends(get_current_user)):

    if not user_id:
        return {"status":"error","message":"not authenticated"}

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT subscription_id FROM users WHERE id=?", (user_id,))
    row = c.fetchone()

    if not row or not row[0]:
        return {"status":"error","message":"no active subscription"}

    subscription_id = row[0]

    try:

        stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )

        return {"status":"success"}

    except Exception as e:

        return {"status":"error","message":str(e)}

# =========================
# Top Modls
# =========================

@app.get("/api/top_models")
def top_models(user=Depends(get_current_user)):

    if not user:
        return {"status": "error", "message": "not authenticated"}

    user_id = user["user_id"]

    if not check_permission(user_id, "view_models"):
        return {"status": "error", "message": "no permission"}

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            model,
            COUNT(*) as count,
            ROUND(AVG(price),2) as median_price,
            MIN(price) as min_price,
            MAX(price) as max_price,
            SUM(
                CASE 
                    WHEN first_seen_time > strftime('%s','now') - 86400
                    THEN 1 
                    ELSE 0 
                END
            ) as velocity
        FROM processed_listings
        WHERE model IS NOT NULL
        AND price BETWEEN 150 AND 600
        GROUP BY model
        ORDER BY count DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()
    conn.close()

    temp = []

    for r in rows:

        model = r[0]
        count = r[1]
        median_price = r[2]
        min_price = r[3]
        max_price = r[4]

        velocity = round((r[5] / count) * 1000, 2)

        volatility = 0

        if median_price:
            volatility = round((max_price - min_price) / median_price, 2)

        demand_score = round(
            velocity * math.log(count + 1),
            2
        )

        raw_score = volatility * demand_score

        temp.append({
            "model": model,
            "count": count,
            "median_price": median_price,
            "velocity": velocity,
            "min_price": min_price,
            "max_price": max_price,
            "volatility": volatility,
            "demand_score": demand_score,
            "raw_score": raw_score
        })

    max_score = max(x["raw_score"] for x in temp) if temp else 1

    result = []

    for x in temp:

        score = round((x["raw_score"] / max_score) * 100, 2) if max_score > 0 else 0
        
        result.append({
            "model": x["model"],
            "count": x["count"],
            "median_price": x["median_price"],
            "velocity": x["velocity"],
            "min_price": x["min_price"],
            "max_price": x["max_price"],
            "volatility": x["volatility"],
            "demand_score": x["demand_score"],
            "arbitrage_score": score
        })

    result.sort(key=lambda x: x["arbitrage_score"], reverse=True)

    return result

# =========================
# Cancel Survey
# =========================

@app.post("/api/cancel_feedback")
def cancel_feedback(
    data: dict,
    user_id: int = Depends(get_current_user)
):

    reason = data.get("reason")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO cancel_feedback (user_id,reason) VALUES (?,?)",
        (user_id, reason)
    )

    conn.commit()
    conn.close()

    return {"status":"saved"}

def check_permission(user_id, permission_name):

    # 🔥 超级管理员（test账号）
    if user_id == 5:
        return True

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT membership_level FROM users WHERE id=?",
        (user_id,)
    )

    result = cursor.fetchone()

    if not result:
        return False

    membership_level = result[0]

    cursor.execute(
        """
        SELECT 1 FROM membership_permissions
        WHERE membership_level=? AND permission_name=?
        """,
        (membership_level, permission_name)
    )

    permission = cursor.fetchone()

    conn.close()

    return permission is not None

@app.get("/api/trend")
def get_trend():

    with open("trend_cache.json") as f:
        data = json.load(f)

    return data

@app.get("/api/revenue")
def get_revenue():

    import stripe
    from datetime import datetime, timedelta

    # 最近30天
    now = datetime.utcnow()
    start = int((now - timedelta(days=30)).timestamp())

    charges = stripe.PaymentIntent.list(
        created={"gte": start},
        limit=100
    )

    total = 0
    count = 0

    for c in charges.data:
        if c.status == "succeeded":
            total += c.amount
            count += 1

    return {
        "total_revenue": round(total / 100, 2),
        "total_orders": count
    }

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):

    return templates.TemplateResponse(
        "admin.html",
        {"request": request}
    )
