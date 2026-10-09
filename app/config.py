import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
DEFAULT_TEAM = os.getenv("DEFAULT_TEAM", "").strip()