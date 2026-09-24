import os, requests, time

W = os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK") or os.getenv("WEBHOOK")

def S(m):
    print(m)
    if not W:
        return
    try:
        requests.post(W, json={"content": m[:1900]}, timeout=15)
    except Exception as e:
        print(e)

def G(url, params=None):
    try:
        for base in ["https://data-api.binance.vision", "https://api.binance.com"]:
            try:
                if "/klines" in url:
                    r = requests.get(base + "/api/v3/klines", params=params, timeout=10)
                elif "/ticker/24hr" in url:
                    r = requests.get(base + "/api/v3/ticker/24hr", timeout=10)
                else:
                    r = requests.get(url, params=params, timeout=10)
                if r.status_code == 200:
                    return r.json()
            except:
                continue
        r = requests.get(url, params=params, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            return r.json()
    except:
        return None
    return None

def GET():
    data = G("https://data-api.binance.vision/api/v3/ticker/24hr")
    if not data:
        data = G("https://api.binance.com/api/v3/ticker/24hr")
    if not data:
        return []

    sigs = []
    for t in data:
        sym = t.get("symbol", "")
        if not sym.endswith("USDT"):
            continue
        if "BUSD" in sym or "USDC" in sym or "FDUSD" in sym:
            continue
        if "BULL" in sym or "BEAR" in sym:
            continue
        try:
            ch = float(t.get("priceChangePercent", 0))
            vol = float(t.get("quoteVolume", 0))
            price = float(t.get("lastPrice", 0))
            if vol < 10000000:
                continue
            if ch < 10 or ch > 60:
                continue
            if price == 0:
                continue

            kl = G("https://data-api.binance.vision/api/v3/klines", params={"symbol": sym, "interval": "15m", "limit": 100})
            if not kl:
                kl = G("https://api.binance.com/api/v3/klines", params={"symbol": sym, "interval": "15m", "limit": 100})
            if not kl:
                continue
            if len(kl) < 99:
                continue

            closes = [float(x[4]) for x in kl]
            ma7 = sum(closes[-7:]) / 7
            ma25 = sum(closes[-25:]) / 25
            ma99 = sum(closes[-99:]) / 99

            if price < ma7:
                continue
            if ma7 < ma25:
                continue
            if ma25 < ma99:
                continue
            if closes[-1] < closes[-2]:
                continue

            entry = price
            sl = ma7 * 0.99
            tp1 = entry * 1.06
            tp2 = entry * 1.10

            rr = (tp1 - entry) / (entry - sl) if entry > sl else 0
            if rr < 1.5:
                continue

            sigs.append((
