# core/config.py
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

PRODUCT_CATALOG_PATH = DATA_DIR / "product_catalog_30.csv"
INVESTOR_DATA_PATH = DATA_DIR / "synthetic_investors_1000_ascii.csv"

# OpenAI config
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"  # or gpt-3.5-turbo if you want
