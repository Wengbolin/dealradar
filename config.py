import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "data" / "market_data.db"

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
