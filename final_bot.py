import requests
import time
from datetime import datetime
import pytz
from flask import Flask
import threading
import os

# ===== TELEGRAM =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.get(url, params={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except:
        pass

# ===== EMA =====
def ema(prices, period):
    if len(prices) < period:
        return None
    k = 2 / (period + 1)
    val = prices[0]
    for p in prices:
        val = p * k + val * (1 - k)
    return val

# ===== DATA =====
def get_prices(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=1d"
        data = requests.get(url, timeout=10).json()
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        return [c for c in closes if c]
    except:
        return []

# ===== SIGNAL MEMORY =====
last_signal = {"NIFTY": None}

# ===== CHECK =====
def check(symbol, name):
    prices = get_prices(symbol)
    if len(prices) < 30:
        return

    e9_prev = ema(prices[-21:-1], 9)
    e15_prev = ema(prices[-21:-1], 15)
    e9_now = ema(prices[-20:], 9)
    e15_now = ema(prices[-20:], 15)

    if not all([e9_prev, e15_prev, e9_now, e15_now]):
        return

    if e9_prev < e15_prev and e9_now > e15_now:
        if last_signal[name] != "BUY":
            send_msg(f"{name} ema crossing")
            last_signal[name] = "BUY"

    elif e9_prev > e15_prev and e9_now < e15_now:
        if last_signal[name] != "SELL":
            send_msg(f"{name} ema crossing")
            last_signal[name] = "SELL"

# ===== TIME =====
def market_open():
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)

    if now.weekday() >= 5:
        return False

    return (9,15) <= (now.hour, now.minute) <= (15,30)

# ===== BOT =====
def run_bot():
    send_msg("Bot started")

    while True:
        tz = pytz.timezone("Asia/Kolkata")
        now = datetime.now(tz)

        if market_open():
            print("Running...")
            check("^NSEI", "NIFTY")
            time.sleep(300)

        else:
            print("Market closed → stopping bot")
            send_msg("Bot stopped (market closed)")
            os._exit(0)   # 🔴 IMPORTANT: STOPS CONTAINER

# ===== WEB (keep alive when needed) =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Running"

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=8080)
