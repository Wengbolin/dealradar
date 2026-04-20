import requests, time, re, json, os
from collections import defaultdict

print("Subito 市场统计 + 策略分析 启动…")

SEARCH_URL = "https://hades.subito.it/v1/search/items?q=iphone&lim=50&sort=datedesc"

STATS_FILE = "model_stats.json"
STATE_FILE = "market_state.json"
CACHE_FILE = "market_cache.json"

MIN_UPDATE_INTERVAL = 1800      # 30分钟
FORCE_UPDATE_INTERVAL = 7200    # 2小时
VOLATILITY_TRIGGER = 0.25       # 25%

model_counts = defaultdict(int)
seen = set()

PATTERN = re.compile(r"iphone\s*(1[0-7])\s*(pro\s*max|pro|max|plus|mini)?", re.I)

def extract_model(text):
    m = PATTERN.search(text)
    if not m:
        return None
    gen = m.group(1)
    suf = (m.group(2) or "").lower().replace(" ","")
    name = f"iphone {gen}"
    if suf:
        name += f" {suf}"
    return name

def load_json(path, default):
    if os.path.exists(path):
        try:
            return json.load(open(path))
        except:
            pass
    return default

def save_stats():
    with open(STATS_FILE,"w",encoding="utf-8") as f:
        json.dump(dict(sorted(model_counts.items(), key=lambda x:-x[1])),f,indent=2,ensure_ascii=False)

last_state = load_json(STATE_FILE,{})
last_cache = load_json(CACHE_FILE,{})
last_update_time = last_state.get("timestamp",0)

def update_strategy(counts):
    global last_update_time,last_cache

    now=time.time()

    # ===== 波动计算 =====
    volatility=0
    if last_cache:
        diffs=[]
        for k in counts:
            old=last_cache.get(k,1)
            new=counts.get(k,1)
            diffs.append(abs(new-old)/max(old,1))
        if diffs:
            volatility=sum(diffs)/len(diffs)

    time_since=now-last_update_time
    should_update=False
    reason=""

    if time_since>=FORCE_UPDATE_INTERVAL:
        should_update=True
        reason="2小时强制更新"
    elif time_since>=MIN_UPDATE_INTERVAL and volatility>=VOLATILITY_TRIGGER:
        should_update=True
        reason="市场波动触发"

    if should_update:

        total=sum(counts.values())

        if total>120:
            min_profit=90
            min_prob=75
            speed="hot"
        elif total>70:
            min_profit=80
            min_prob=65
            speed="normal"
        else:
            min_profit=65
            min_prob=55
            speed="cold"

        state={
            "timestamp":now,
            "market_speed":speed,
            "recommended_min_profit":min_profit,
            "recommended_probability":min_prob,
            "volatility":round(volatility,2)
        }

        json.dump(state,open(STATE_FILE,"w"),indent=2)
        print("策略更新:",reason,state)

        last_update_time=now

    json.dump(counts,open(CACHE_FILE,"w"),indent=2)
    last_cache=counts.copy()

while True:
    try:
        ads = requests.get(SEARCH_URL, timeout=10).json().get("ads", [])
        print("抓到:",len(ads))

        round_counts=defaultdict(int)

        for ad in ads:
            url = ad.get("urls",{}).get("default")
            if not url or url in seen:
                continue
            seen.add(url)

            text=(ad.get("subject","")+" "+ad.get("body",""))
            model=extract_model(text)

            if model:
                model_counts[model]+=1
                round_counts[model]+=1

        save_stats()
        update_strategy(round_counts)

        time.sleep(300)

    except Exception as e:
        print("错误:",e)
        time.sleep(10)

