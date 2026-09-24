import os
import requests

W = os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK") or os.getenv("WEBHOOK")

def S(m):
    print(m)
    if W is None:
        return
    try:
        requests.post(W, json={"content": m[:1900]}, timeout=15)
    except:
        pass

def G(url, params=None):
    try:
        for base in ["https://data-api.binance.vision", "https://api.binance.com"]:
            try:
                if "klines" in url:
                    r = requests.get(base + "/api/v3/klines", params=params, timeout=10)
                else:
                    r = requests.get(base + "/api/v3/ticker/24hr", timeout=10)
                if r.status_code == 200:
                    return r.json()
            except:
                continue
    except:
        return None
    return None

def calc_ma(arr, period):
    total = 0
    n = len(arr)
    for i in range(period):
        total = total + arr[n - 1 - i]
    return total / period

def GET():
    data = G("https://data-api.binance.vision/api/v3/ticker/24hr")
    if not data:
        return []
    sigs = []
    for t in data:
        sym = t.get("symbol", "")
        if not sym.endswith("USDT"):
            continue
        if "BUSD
