import requests
import sqlite3
import time

ACCESS_TOKEN = "v^1.1#i^1#r^0#f^0#p^1#I^3#t^H4sIAAAAAAAA/+VYbWwURRjutVe0qUBSSKloynULQcG9m93b27vd9I5cP0iL0NbeUdsiwf2YLUv3dped3V4PozblI+BHsBgR4Qcl4YeCmv7SGgSiJkYMQYkSQWMIUcB/qIkSiEFnr6W0lVCkZ2zi/bnMzDvvvM/zPu/M7IDeGUVLttVvuzrTc1/+QC/ozfd4qGJQNKNw6ayC/PmFeWCMgWegd2Gvt6/gpyokpDSTb4HINHQEfT0pTUd8tjNKOJbOGwJSEa8LKYh4W+IT8VUredoPeNMybEMyNMLXUBslwjIb4egIFFkuxIoKhXv1mz6TRpSALAfCHBA4IRIMAsDhcYQc2KAjW9DtKEEDmiVBkKTYJE3zIcDTIT/LMR2ErxVaSDV0bOIHRCwbLp+da42J9c6hCghBy8ZOiFhDfHmiKd5QW9eYrAqM8RUb4SFhC7aDxrdqDBn6WgXNgXdeBmWt+YQjSRAhIhAbXmG8Uz5+M5h7CD9LNYxw4bDESFIQMMEwC3JC5XLDSgn2neNwe1SZVLKmPNRt1c5MxihmQ9wAJXuk1YhdNNT63L8nHEFTFRVaUaKuOt4eb24mYqKhqXoa6mQtFLQWQRbI5pZaMiIqYYajFZFkwpyMVcSMLDTsbYTmCSvVGLqsuqQhX6NhV0McNZzIDTOGG2zUpDdZccV2Ixq1CycBuMlhJNLhJnU4i469XnfzClOYCF+2OXkGRmfbtqWKjg1HPUwcyFIUJQTTVGVi4mBWiyPy6UFRYr1tm3wgkE6n/emg37A6AzQAVKBt1cqEtB6mBALburU+bK9OPoFUs1AkiGcilbczJo6lB2sVB6B3ErEQSzMMPcL7+LBiE3v/1jEGc2B8ReSqQoKRkMQoEVcstARhTjab2IhIA24cUBQyZEqwuqBtaoIESQnrzElBS5X5YEihgxEFkjLLKSTDKQophmSWpBQIAYSiKHGR/1Oh3K3UE1CyoJ0TredM541idbJVZdJ1lNmwUU42p1cgh01t0tme1UmuXsi0bqhhVm2IrMbVEL3bargt+BpNxcwk8fq5IMCt9dyRUG8gG8pTgpeQDBM2Y81KmemV4KAlNwuWnUlADRdU55RAxk2zITd7dc7g/cNt4t5w5+6M+o/Op9uiQq5kpxcqdz7CDgRT9bsnkF8yUgG31g0BXz/c7nXZqKeEW8U312mFGoMcRqvKw1dOfxauH3VLfgsiw7Hwbdvf5N7AkkYX1PF5ZluGpkGrlZpyPadSji2IGpxuhZ0DgavCNDtsqXA4GAYUQ4emhEvKHqXrptuWlIut2NvnqZgUfwv2n5pe2E3LkB3JvWP+C58MgfEPGLG87I/q83wM+jzH8j0eUAUWUZWgYkbBam/BA/ORakO/Kih+pHbq+Lvcgv4umDEF1cqfk/f5mXON5UdWvLnjx3m9WxcGduXNGvN+MrAWlI2+oBQVUMVjnlPAw7dGCqnZ82bSLAhSLE2HAB3qAJW3Rr1UqXfuq2VbgP/IM4HBtOg9VXCs4Pif5Fkwc9TI4ynMw8nO2/hD2ZoPq9Jw9vVla3d7fx6s5060fnNCbgvmeU8db3vtwtXnTw21Kc7cD9pLFt/YU7Hj0aX5F+KH0dGSJaWHrg31Xyu5dLTygHhgzeYnu7eXnFS49i9KB6+UfPb+t+a8/gWb9x0g93uL71809Oxv8K2XhD5u/+K3N7Ue37uzvGP3QzdelB5beuV8Ha0WdT734HVS27vy0LsLGjvLPyrqnnWp9Oi5GTsP9u+7tOxs5Xed13Ym+3/f8svgGngyvedk1cW9meLKZV3dL6TYQ/T3bwxVaOjpFZ/qT5XNSZze3Hb+zNbg2se7tl4e+LXdOTh48XK5Wpw4zBC7/nj561faTn91om9w+zvvffLIl69X+4Zz+RexBS642RIAAA=="

url = "https://api.ebay.com/buy/browse/v1/item_summary/search"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "X-EBAY-C-MARKETPLACE-ID": "EBAY_IT"
}

conn = sqlite3.connect("../data/market_data.db")
cursor = conn.cursor()

limit = 50
pages = 10

print(">>> 抓取 eBay")

for page in range(pages):

    params = {
        "q": "iphone",
        "limit": limit,
        "offset": page * limit
    }

    print(f">>> eBay 第 {page+1} 页")

    response = requests.get(url, headers=headers, params=params)

    print("status:", response.status_code)

    data = response.json()

    items = data.get("itemSummaries", [])

    print(">>> 本页", len(items), "条")

    for item in items:

        title = item["title"]
        title_lower = title.lower()

        # ===== 过滤非整机（非常关键）=====
        if any(x in title_lower for x in [
            "cover", "custodia", "vetro", "display",
            "batteria", "battery", "protector",
            "flex", "ricambio", "lcd", "screen",
            "case", "glass"
        ]):
            continue

        # 可选：只保留 iPhone
        if "iphone" not in title_lower:
            continue
        # ==================================

        price = float(item["price"]["value"])
        url_item = item["itemWebUrl"]

        item_id = item["itemId"]

        now = time.time()

        cursor.execute("""
        INSERT OR IGNORE INTO listings
        (item_id,title,price,url,first_seen_time,last_seen_time,is_active)
        VALUES (?,?,?,?,?,?,1)
        """,(
            item_id,
            title,
            price,
            url_item,
            now,
            now
        ))

        print("写入:",title,price)

    time.sleep(1)

conn.commit()
conn.close()

print(">>> eBay 抓取完成")
