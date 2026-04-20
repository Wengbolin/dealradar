from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time,re,statistics

# ========= 连接浏览器 =========
def attach():
    while True:
        try:
            opt=Options()
            opt.debugger_address="127.0.0.1:9222"
            d=webdriver.Chrome(options=opt)
            print("已连接浏览器")
            return d
        except:
            print("等待浏览器...")
            time.sleep(3)

driver=attach()

# ========= 风险词 =========
BAD=[
"difetto","rotto","ricambi","bloccato","icloud","non funziona",
"guasto","display","schermo","per pezzi","solo scheda"
]

# ========= 解析型号 =========
def parse_model(title):
    t=title.lower()

    # 型号
    m=re.search(r'iphone\s?(\d{1,2})',t)
    if not m:
        return None
    model=m.group(1)

    # pro / mini / plus
    variant=""
    if "pro max" in t: variant="pro max"
    elif "pro" in t: variant="pro"
    elif "mini" in t: variant="mini"
    elif "plus" in t: variant="plus"

    # 容量
    s=re.search(r'(64|128|256|512|1tb)\s?gb',t)
    if not s:
        return None
    storage=s.group(1)

    return f"{model}-{variant}-{storage}"

seen=set()

# ========= 打开聊天 =========
def contact(link,title):
    try:
        driver.execute_script("window.open(arguments[0]);",link)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(6)

        # 没聊天框=商家
        if "Mostra numero" in driver.page_source:
            print("商家广告，跳过")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            return

        buttons=driver.find_elements(By.TAG_NAME,"button")
        for b in buttons:
            if "contatta" in b.text.lower() or "messaggio" in b.text.lower():
                b.click()
                break

        time.sleep(2)
        textarea=driver.find_element(By.TAG_NAME,"textarea")
        textarea.send_keys(f"Ciao! Ho visto '{title}', è ancora disponibile?")

        print("👉 已填写消息，请手动发送")

        time.sleep(8)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    except:
        print("联系失败")

# ========= 滚动 =========
def scroll():
    last=0
    for _ in range(10):
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        time.sleep(2)
        new=driver.execute_script("return document.body.scrollHeight")
        if new==last: break
        last=new

# ========= 扫描 =========
def scan():
    scroll()

    cards=driver.find_elements(By.CSS_SELECTOR,"article")
    print("发现:",len(cards))

    market={}

    # 先收集价格
    for c in cards:
        try:
            title=c.find_element(By.TAG_NAME,"h3").text
            if any(b in title.lower() for b in BAD):
                continue

            key=parse_model(title)
            if not key:
                continue

            price=int(re.sub(r'\D','',c.find_element(By.CSS_SELECTOR,"p").text))
            market.setdefault(key,[]).append(price)

        except:
            pass

    # 再找低价
    for c in cards:
        try:
            title=c.find_element(By.TAG_NAME,"h3").text
            link=c.find_element(By.CSS_SELECTOR,"a[href*='/telefonia/iphone']").get_attribute("href")

            if link in seen:
                continue

            key=parse_model(title)
            if not key or key not in market or len(market[key])<4:
                continue

            price=int(re.sub(r'\D','',c.find_element(By.CSS_SELECTOR,"p").text))
            avg=int(statistics.mean(market[key]))
            diff=(avg-price)/avg

            if diff>=0.20:
                print(f"\n🔥 真捡漏 {key}  {price}€  市场{avg}")
                print(title)
                seen.add(link)
                contact(link,title)

            elif diff>=0.12:
                print(f"⭐ 可关注 {key} {price}€ 市场{avg}")

        except:
            pass

# ========= 主循环 =========
while True:
    try:
        scan()
        print("等待60秒...\n")
        time.sleep(60)
        driver.refresh()
    except:
        driver=attach()

