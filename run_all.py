import subprocess
import time
from datetime import datetime

print("🚀 DealRadar System Started")

while True:
    print("\n==============================")
    print("⏱ 时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("==============================")

    try:
        print("📡 Step 1: 抓取数据 (hunter)")
        subprocess.run(["python", "iphone_hunter.py"], check=True)

        print("📊 Step 3: 生成缓存 (cache)")
        subprocess.run(["python", "generate_arbitrage_cache.py"], check=True)

        print("✅ 本轮完成，休眠60秒...\n")

    except Exception as e:
        print("❌ 出错:", e)

    time.sleep(60)
