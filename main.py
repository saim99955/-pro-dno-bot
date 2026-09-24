import os
import requests
import time

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

def GET():
    data = G("https://data-api.binance.vision/api/v3/ticker/24hr")
    if not data:
        return []
    sigs = []
    for t in data:
        sym = t.get("symbol", "")
        if not sym.endswith("USDT"):
            continue
        if "BUSD" in sym or "USDC" in sym or "FDUSD" in sym:
            continue
        try:
            ch = float(t.get("priceChangePercent", 0))
            vol = float(t.get("quoteVolume", 0))
            price = float(t.get("lastPrice", 0))
            if vol < 10000000:
                continue
            if ch < 12 or ch > 60:
                continue
            if price == 0:
                continue
            kl = G("https://data-api.binance.vision/api/v3/klines", params={"symbol": sym, "interval": "15m", "limit": 100})
            if not kl or len(kl) < 99:
                continue
            closes = []
            for x in kl:
                closes.append(float(x[4]))
            ma7 = sum(closes
