import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)   # ⭐ 关键：自动创建目录

DB_PATH = BASE_DIR / "data" / "market_data.db"

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
