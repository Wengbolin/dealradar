# =========================
# 🧠 Decision Engine V1.0
# 带资金分配 + 风控 + 正确流程
# =========================


# =========================
# 🔧 参数配置（后期可调优）
# =========================
MAX_POSITIONS = 3          # 最大同时持仓
RESERVE_RATIO = 0.3        # 保留现金 30%

HIGH_RISK_RATIO = 0.1
MEDIUM_RISK_RATIO = 0.2
LOW_RISK_RATIO = 0.35


# =========================
# 🧠 容量偏好（影响评分）
# =========================
def storage_preference_bonus(storage):

    if not storage:
        return 0

    if storage == 128:
        return 10

    if storage == 256:
        return 5

    if storage >= 512:
        return -10

    if storage <= 64:
        return -5

    return 0


# =========================
# 🧠 风险评估（改进版）
# =========================
def estimate_risk(confidence, profit, score, title=""):

    title_lower = str(title).lower()

    # 🔥 可疑关键词（欧洲二手常见）
    suspicious_keywords = [
        "leggi bene",   # 仔细看（常见坑）
        "solo",         # 仅限（可能有条件）
        "bloccato",     # 锁机
        "icloud",       # iCloud问题
        "non funziona", # 不工作
        "per pezzi",    # 配件机
        "rotto"         # 坏的
    ]

    # 🔥 命中关键词 → 高风险
    for kw in suspicious_keywords:
        if kw in title_lower:
            return "HIGH"

    # 🔥 正常风险判断（以流动性为主）
    if confidence >= 25:
        return "LOW"

    if confidence >= 18:
        return "MEDIUM"

    return "HIGH"

# =========================
# 🧠 卖出时间（增强版）
# =========================
def estimate_sell_time(confidence, model, score):

    model_lower = str(model).lower()

    # 🔥 小众机 / 冷门机（慢）
    if "mini" in model_lower:
        return "5-10 days"

    # 🔥 高评分 + 高流动性 → 快
    if confidence >= 22 and score >= 55:
        return "1-2 days"

    # 🔥 中等
    if confidence >= 18 and score >= 50:
        return "2-3 days"

    # 🔥 一般
    if confidence >= 15:
        return "3-5 days"

    # 🔥 慢
    return "5-10 days"


# =========================
# 🧠 决策判断（收紧版）
# =========================
def make_decision_label(profit, score, confidence):

    # 🔥 主力 BUY（稳定赚钱）
    if profit >= 70 and score >= 50 and confidence >= 18:
        return "BUY"

    # 🟡 次级 BUY（少量参与）
    if profit >= 55 and score >= 48 and confidence >= 20:
        return "BUY"

    # 👀 观察
    if profit >= 40 and score >= 42:
        return "WATCH"

    return "SKIP"


# =========================
# 💰 资金分配（核心）
# =========================
def calculate_invest_amount(capital, risk, active_positions):

    # 🔥 控制持仓数量
    if active_positions >= MAX_POSITIONS:
        return 0

    available_capital = capital * (1 - RESERVE_RATIO)

    if risk == "LOW":
        return round(available_capital * LOW_RISK_RATIO, 2)

    elif risk == "MEDIUM":
        return round(available_capital * MEDIUM_RISK_RATIO, 2)

    else:
        return round(available_capital * HIGH_RISK_RATIO, 2)


# =========================
# 🧠 主函数（正确流程）
# =========================
def make_decision(deal, capital=500, active_positions=0):

    profit = deal.get("profit", 0)
    score = deal.get("score", 0)
    confidence = deal.get("confidence", 0)
    model = deal.get("model", "")
    storage = deal.get("storage", None)
    price = deal.get("price", 0)
    title = deal.get("title", "")

    # 1️⃣ 修正评分（容量影响）
    score += storage_preference_bonus(storage)

    # 2️⃣ 决策（能不能买）
    decision = make_decision_label(profit, score, confidence)

    # 🔥 A级机会强制优先（绝不错过好单）
    is_top_deal = (
        profit >= 70 and
        confidence >= 18 and
        score >= 55
    )

    if is_top_deal:
        decision = "BUY"

    # 3️⃣ 风险评估
    risk = estimate_risk(confidence, profit, score, title)
    # 🔥 高风险自动降级（防止踩坑）
    if risk == "HIGH":
        if profit >= 90:
            decision = "WATCH"   # 超高利润才允许观察
        else:
            decision = "SKIP"


    # 4️⃣ 卖出时间
    sell_time = estimate_sell_time(confidence, model, score)

    # 5️⃣ 资金分配（€）
    invest_amount = 0

    if decision == "BUY":
        invest_amount = calculate_invest_amount(
            capital,
            risk,
            active_positions
        )

        # 🔥 钱不够 → 强制降级
        if invest_amount < price:

            # 🔥 如果是优质单 → 强制最低仓位买入
            if risk == "LOW" or (profit >= 70 and confidence >= 18):
                invest_amount = price   # 最少买1台

            else:
                decision = "SKIP"
                invest_amount = 0

    return {
        "decision": decision,
        "risk": risk,
        "sell_time": sell_time,
        "invest_eur": invest_amount
    }
