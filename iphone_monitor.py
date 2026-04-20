import requests
import time
import re
from collections import defaultdict

URL = "https://hades.subito.it/v1/search/items"

HEADERS = {
    "accept": "application/json",
    "accept-language": "it-IT,it;q=0.9",
    "origin": "https://www.subito.it",
    "referer": "https://www.subito.it/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

market_price = defaultdict(list)


def parse_iphone(title):
    title = title.lower()

    model = None
    storage = None

    m = re.search(r'iphone\s?(se|x|xr|xs|max|11|12|13|14|15)(\s?(pro|max|mini)?)', title)
    if m:
        model = "iphone " + m.group(1) + m.group(2)

    s = re.search(r'(64|128|256|512|1tb)\s?gb', title)
    if s:
        storage = s.group(1) + "gb"

    if model and storage:
        return model + " " + storage
    return None


def get_items(start):
    params = {
        "q": "iphone",
        "r": "4",
        "shp": "false",
        "urg": "false",
        "sort": "datedesc",
        "lim": "30",
        "start": str(start)
    }

    r = requests.get(URL, headers=HEADERS, params=params, timeout=20)

    if r.status_code != 200:
        print("请求失败:", r.status_code)
        return []

    data = r.json()
    return data.get("items", [])


def scan():
    print("\n扫描市场...")

    all_items = []
    for start in range(0, 120, 30):
        items = get_items(start)
        all_items.extend(items)

    print("获取到商品:", len(all_items))

    for item in all_items:
        title = item.get("subject", "")
        price = item.get("price", {}).get("value")
        link = "https://www.subito.it" + item.get("url", "")

        if not price:
            continue

        key = parse_iphone(title)
        if not key:
            continue

        market_price[key].append(price)
        avg = sum(market_price[key]) / len(market_price[key])

        if len(market_price[key]) > 6 and price < avg * 0.7:
            print("\n🔥发现低价🔥")
            print("型号:", key)
            print("价格:", price, "€")
            print("市场均价:", int(avg), "€")
            print(link)


while True:
    try:
        scan()
        print("等待60秒...")
        time.sleep(60)
    except Exception as e:
        print("错误:", e)
        time.sleep(10)

