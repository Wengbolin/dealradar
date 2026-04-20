import json
from collections import defaultdict

def analyze_market(deals):

    model_profit = defaultdict(list)
    model_risk = defaultdict(list)

    for d in deals:

        model = d.get("model")
        profit = d.get("profit", 0)
        risk = d.get("risk")

        model_profit[model].append(profit)
        model_risk[model].append(risk)

    summary = []

    for model in model_profit:

        avg_profit = sum(model_profit[model]) / len(model_profit[model])
        high_risk_count = model_risk[model].count("HIGH")

        summary.append({
            "model": model,
            "avg_profit": round(avg_profit, 1),
            "risk_count": high_risk_count
        })

    return summary


def get_market_control(deals):

    summary = analyze_market(deals)

    # 🔥 最赚钱（排序）
    top_models = sorted(summary, key=lambda x: x["avg_profit"], reverse=True)

    # ⚠️ 高风险
    risky_models = [m for m in summary if m["risk_count"] >= 1]

    return {
        "top_models": top_models[:3],
        "risky_models": risky_models
    }

def generate_strategy(deals):

    model_data = {}

    for d in deals:

        model = d.get("model")
        decision = d.get("decision")
        risk = d.get("risk")
        profit = d.get("profit", 0)

        if model not in model_data:
            model_data[model] = {
                "profits": [],
                "buy_count": 0,
                "risk_count": 0
            }

        if decision == "BUY":
            model_data[model]["profits"].append(profit)
            model_data[model]["buy_count"] += 1

        if risk == "HIGH":
            model_data[model]["risk_count"] += 1

    results = []

    for model, data in model_data.items():

        avg_profit = sum(data["profits"]) / len(data["profits"]) if data["profits"] else 0

        # 🔥 核心判断（净结果）
        if data["risk_count"] > data["buy_count"]:
            action = "AVOID"

        elif data["buy_count"] > 0:
            action = "BUY"

        else:
            action = "SKIP"

        # 🔥 信号强度（核心）
        strength = "LOW"

        if avg_profit >= 70 and data["buy_count"] >= 1:
            strength = "STRONG"

        elif avg_profit >= 50:
            strength = "MEDIUM"


        results.append({
            "model": model,
            "action": action,
            "avg_profit": round(avg_profit, 1),
            "strength": strength
        })

    # 🔥 排序（优先赚钱）
    results.sort(key=lambda x: x["avg_profit"], reverse=True)

    return results

if __name__ == "__main__":

    with open("arbitrage_cache.json", "r") as f:
        deals = json.load(f)

    market = get_market_control(deals)
    strategy = generate_strategy(deals)

    print("\n📊 MARKET CONTROL")
    print("====================")

    print("\n🔥 Top Models:")
    for m in market["top_models"]:
        print(f"{m['model']} | avg_profit: {m['avg_profit']}€")

    print("\n⚠️ Risky Models:")
    for m in market["risky_models"]:
        print(f"{m['model']} | high_risk_count: {m['risk_count']}")

    print("\n🎯 TODAY STRATEGY")
    print("====================")

    strategy = generate_strategy(deals)

    for s in strategy:
         print(f"{s['model']} → {s['action']} | {s['strength']} | {s['avg_profit']}€")
