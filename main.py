import os, requests, time

W = os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK") or os.getenv("WEBHOOK")
print(f"Webhook: {'OK' if W else 'MISSING'}")

def S(m):
    print(m)
    if not W: return
    try:
        requests.post(W, json={"content": m[:1900]}, timeout=15)
    except Exception as e:
        print(f"Discord err {e}")

def G(url, params=None):
    try:
        for base in ["https://data-api.binance.vision", "https://api.binance.com"]:
            try:
                if "/klines" in url:
                    r = requests.get(f"{base}/api/v3/klines", params=params, timeout=10)
                elif "/ticker/24hr" in url:
                    r = requests.get(f"{base}/api/v3/ticker/24hr", timeout=10)
                elif "/ticker/price" in url:
                    r = requests.get(f"{base}/api/v3/ticker/price", params=params, timeout=10)
                else:
                    r = requests.get(url, params=params, timeout=10)
                if r.status_code==200:
                    return r.json()
            except: continue
        r = requests.get(url, params=params, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code==200:
            return r.json()
    except: return None
    return None

def GET_SIGNAL():
    data = G("https://data-api.binance.vision/api/v3/ticker/24hr")
    if not data:
        data = G("https://api.binance.com/api/v3/ticker/24hr")
    if not data: 
        return []

    signals=[]
    for t in data:
        sym=t.get('symbol','')
        if not sym.endswith('USDT'): continue
        if any(x in sym for x in ['BUSD','USDC','FDUSD','BULL','BEAR']): continue
        try:
            ch = float(t.get('priceChangePercent',0))
            vol = float(t.get('quoteVolume',0))
            price = float(t.get('
