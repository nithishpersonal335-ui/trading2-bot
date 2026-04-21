import requests
import time
from datetime import datetime
import pytz
from flask import Flask
import threading

# ===== TELEGRAM =====
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

BOT_ACTIVE = False  # 🔴 switch

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

last_signal = None

def check():
    global last_signal

    prices = get_prices("^NSEI")
    if len(prices) < 30:
        return

    e9_prev = ema(prices[-21:-1], 9)
    e15_prev = ema(prices[-21:-1], 15)

    e9_now = ema(prices[-20:], 9)
    e15_now = ema(prices[-20:], 15)

    if not all([e9_prev, e15_prev, e9_now, e15_now]):
        return

    if e9_prev < e15_prev and e9_now > e15_now:
        if last_signal != "BUY":
            send_msg("NIFTY ema crossing")
            last_signal = "BUY"

    elif e9_prev > e15_prev and e9_now < e15_now:
        if last_signal != "SELL":
            send_msg("NIFTY ema crossing")
            last_signal = "SELL"

# ===== TELEGRAM COMMANDS =====
last_update_id = None

def check_commands():
    global BOT_ACTIVE, last_update_id

    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        res = requests.get(url, timeout=10).json()

        for update in res.get("result", []):
            uid = update["update_id"]

            if last_update_id is not None and uid <= last_update_id:
                continue

            last_update_id = uid

            msg = update.get("message", {}).get("text", "").lower()

            if "/on" in msg:
                BOT_ACTIVE = True
                send_msg("Bot turned ON ✅")

            elif "/off" in msg:
                BOT_ACTIVE = False
                send_msg("Bot turned OFF 🛑")

    except:
        pass

# ===== BOT LOOP =====
def run_bot():
    print("Bot Started")
    send_msg("Cloud bot ready ✅")

    while True:
        try:
            check_commands()  # 👈 check ON/OFF

            if BOT_ACTIVE:
                print("Bot ACTIVE → checking market")
                check()
                time.sleep(300)

            else:
                print("Bot OFF → idle")
                time.sleep(10)

        except Exception as e:
            print("Error:", e)
            time.sleep(30)

# ===== WEB SERVER =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running"

# ===== START =====
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=8080)
