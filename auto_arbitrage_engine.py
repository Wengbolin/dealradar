import time
import subprocess

print("DealRadar Auto Arbitrage Engine Started")

while True:

    print("================================")
    print("DealRadar Market Scan Starting")
    print("================================")

    # 1 采集市场数据
    print("Step 1: Collect market data")
    subprocess.run(["python", "market_collector.py"])

    # 2 数据处理（型号识别）
    print("Step 2: Process listings")
    subprocess.run(["python", "data_processing_engine.py"])

    # 3 更新价格指数
    print("Step 3: Update price index")
    subprocess.run(["python", "price_index_engine.py"])

    # 4 生成套利机会
    print("Step 4: Generate arbitrage")
    subprocess.run(["python", "generate_arbitrage_cache.py"])

    print("DealRadar Scan Complete")

    # 每60秒扫描一次
    print("Next scan in 60 seconds")
    time.sleep(60)
