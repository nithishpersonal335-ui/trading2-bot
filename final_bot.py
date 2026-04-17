import requests
import time
from datetime import datetime

BOT_TOKEN = "8285229070:AAGZQnCbjULqMUsZkmNMBSG9NCh3WlI2bNo"
CHAT_ID = "1207682165"

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.get(url, params={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except:
        print("Telegram error")

def ema(prices, period):
    if len(prices) < period:
        return None
    k = 2 / (period + 1)
    ema_val = prices[0]
    for p in prices:
        ema_val = p * k + ema_val * (1 - k)
    return ema_val

def get_prices(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=1d"
        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            return []

        data = r.json()
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        return [c for c in closes if c is not None]

    except:
        return []

last_signal = {
    "NIFTY": None,
    "BANKNIFTY": None,
    "SENSEX": None
}

def check(symbol, name):
    prices = get_prices(symbol)

    if len(prices) < 30:
        return

    ema9_prev = ema(prices[-21:-1], 9)
    ema15_prev = ema(prices[-21:-1], 15)

    ema9_now = ema(prices[-20:], 9)
    ema15_now = ema(prices[-20:], 15)

    if not all([ema9_prev, ema15_prev, ema9_now, ema15_now]):
        return

    if ema9_prev < ema15_prev and ema9_now > ema15_now:
        if last_signal[name] != "BUY":
            send_msg(f"{name} ema crossing")
            last_signal[name] = "BUY"

    elif ema9_prev > ema15_prev and ema9_now < ema15_now:
        if last_signal[name] != "SELL":
            send_msg(f"{name} ema crossing")
            last_signal[name] = "SELL"

def is_market_open():
    now = datetime.now()
    start = now.replace(hour=9, minute=15, second=0)
    end = now.replace(hour=15, minute=30, second=0)
    return start <= now <= end

print("Bot Started...")

while True:
    try:
        if is_market_open():
            print("Checking...")

            check("^NSEI", "NIFTY")
            check("^NSEBANK", "BANKNIFTY")
            check("^BSESN", "SENSEX")

            time.sleep(300)

        else:
            print("Market closed")
            time.sleep(60)

    except Exception as e:
        print("Error:", e)
        time.sleep(60)
