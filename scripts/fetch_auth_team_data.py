import requests
import os
from dotenv import load_dotenv

load_dotenv()

url = "https://fantasy.formula1.com/services/user/gameplay/00190f2c-133c-11f1-9186-ede0d682ac23/getteam/1/1/5/1"

headers = {
    "accept": "application/json, text/plain, */*",
    "referer": "https://fantasy.formula1.com/",
    "user-agent": os.getenv("F1_USER_AGENT"),
    "cookie": os.getenv("F1_COOKIE"),
}

r = requests.get(url, headers=headers)

print(r.status_code)

data = r.json()