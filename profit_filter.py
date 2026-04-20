import re

ACCESSORY_KEYWORDS = [
    "display","lcd","vetro","cover","custodia","batteria","ricambi","scocca",
    "frame","camera","cavo","cable","usb","tasto","flex","compatibile",
    "ricambio","parte","pellicola","protezione","scatola","box","solo scatola",

    "vetro temperato","tempered","protector","glass","screen",
    "porta sim","sim tray","housing","back cover","front glass",
    "ricambio iphone","ricambi iphone","pezzi iphone","parte iphone",
    "kit riparazione","repair kit","strumenti riparazione",
    "supporto auto","car holder","support","stand",
    "cuffie","auricolari","earbuds","airpods case",
    "caricatore","caricabatterie","charger","charging cable",
    "magnetico","magnetic","dock","adattatore","adapter",

    "accessori",
    "schermo",
    "scheda madre",
    "motherboard",
    "madre",
    "pezzi",
    "per ricambi",
    "ricambi apple",
    "ricambi iphone"
]

MULTI_ITEM_KEYWORDS = [
    "+"," con ","insieme","lotto","stock","scambio","permuto"
]

BAD_PHONE_KEYWORDS = [
    "icloud","bloccato","mdm","solo wifi","no imei","senza imei",
    "per pezzi","da riparare","rotto","non funziona","broken",
    "solo scheda","solo motherboard","solo logica",

    "da sistemare",
    "non si accende",
    "schermo rotto",
    "display rotto",
    "vetro rotto",
    "touch non funziona",
    "face id non funziona",
    "senza face id",
    "batteria da cambiare",
    "problema scheda",
    "problema logica",
    "bloccato icloud",

    "display da cambiare",
    "touch rotto",
    "batteria scarica",
    "no display",
    "solo telefono",
    "solo scocca"
]


def contains_keyword(text, keywords):

    text = text.lower()

    for k in keywords:
        if k in text:
            return True

    return False


# =========================
# 型号识别
# =========================
def extract_model(title):

    t = title.lower().replace(" ", "")

    if "iphone14promax" in t:
        return "iPhone 14 Pro Max"

    if "iphone14pro" in t:
        return "iPhone 14 Pro"

    if "iphone14plus" in t:
        return "iPhone 14 Plus"

    if "iphone14" in t:
        return "iPhone 14"

    if "iphone13promax" in t:
        return "iPhone 13 Pro Max"

    if "iphone13pro" in t:
        return "iPhone 13 Pro"

    if "iphone13mini" in t:
        return "iPhone 13 Mini"

    if "iphone13" in t:
        return "iPhone 13"

    if "iphone12promax" in t:
        return "iPhone 12 Pro Max"

    if "iphone12pro" in t:
        return "iPhone 12 Pro"

    if "iphone12mini" in t:
        return "iPhone 12 Mini"

    if "iphone12" in t:
        return "iPhone 12"

    return None


def extract_storage(text):

    text = text.lower()

    m = re.search(r"\b(64|128|256|512|1024|1tb)\s?(g|gb|tb|giga)?\b", text)

    if not m:
        return None

    val = m.group(1)

    if val in ("1tb", "1024"):
        return "1024"

    return val


def negotiation_coeff(title, desc):

    text = (title + " " + desc).lower()

    if "rotto" in text:
        return 0.6

    if "urgente" in text:
        return 0.7

    if "perfetto" in text:
        return 0.9

    return 0.8


# =========================
# 主判断函数
# =========================

def is_profitable(title, desc, price):

    # 只保留最关键过滤（防止垃圾数据）
    if price < 50:
        return False, 0, "价格异常"

    text = (title + " " + desc).lower()

    # 只过滤致命问题
    if "icloud" in text or "mdm" in text:
        return False, 0, "锁机"

    model = extract_model(title)

    if not model:
        return False, 0, "无法识别型号"

    # 👉 不再做利润判断
    return True, 0, "通过基础过滤"


import re

def extract_storage(title):

    title = title.lower()

    match = re.search(r'(\d+)\s?(gb|g|tb)', title)

    if not match:
        return None

    size = int(match.group(1))
    unit = match.group(2)

    # TB 转 GB
    if unit == "tb":
        size = size * 1024

    # 🔥 只允许合理容量（核心过滤）
    VALID_SIZES = {64, 128, 256, 512, 1024}

    if size not in VALID_SIZES:
        return None

    return size
