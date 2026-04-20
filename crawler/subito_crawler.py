import requests
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

SEARCH_BASE = "https://hades.subito.it/v1/search/items?q=iphone&lim=50&sort=datedesc"

MAX_PAGES = 40

def fetch_ads():

    all_ads = []

    for page in range(MAX_PAGES):

        offset = page * 50

        url = f"{SEARCH_BASE}&offset={offset}"

        print(f">>> 抓取 Subito 第 {page+1} 页")

        try:

            r = requests.get(url, headers=HEADERS, timeout=10)

            if r.status_code != 200:
                print("HTTP ERROR:", r.status_code)
                break

            ads = r.json().get("ads", [])

        except Exception as e:

            print("请求错误:", e)
            break

        if not ads:
            print(">>> 没有更多数据")
            break

        print(f">>> 本页 {len(ads)} 条")

        all_ads.extend(ads)

        time.sleep(0.4)

    print(f">>> Subito 总抓取 {len(all_ads)} 条")

    return all_ads
