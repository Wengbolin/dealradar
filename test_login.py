from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

options = webdriver.ChromeOptions()

# 关键：使用独立机器人目录
options.add_argument("--user-data-dir=/Users/mac/Library/Application Support/Google/Chrome/BOT_PROFILE")

# 关键：mac 必须远程调试端口，否则100%崩
options.add_argument("--remote-debugging-port=9222")

# 防止Mac权限阻止
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# 稳定性
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

driver.get("https://www.subito.it")

print("浏览器已启动，60秒内手动操作登录")
time.sleep(60)



