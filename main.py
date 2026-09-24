import os, requests, math
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK")

def send(m):
    try:
        requests.post(WEBHOOK, json={"content": m}, timeout=15)
    except: pass

def safe_get(u):
    try:
        r = requests.get(u, timeout=12, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code == 200: return r.json()
    except Exception as e:
        print(e)
    return None

def get_klines(sym, tf="15m", lim=200):
    for url in [
        f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval={tf}&limit={lim}",
        f"https://api.binance.com/api/v3/klines?symbol={sym}&interval={tf}&limit={lim}"
    ]:
        j = safe_get(url)
        if j and len(j) > 100:
            closes = [float(x[4]) for x in j]
            vols = [float(x[5]) for x in j]
            highs = [float(x[2]) for x in j]
            lows = [float(x[3]) for x in j]
            return closes, vols, highs, lows
    return None

def calc(closes, highs, lows, vols):
    def ema(data, p):
        k = 2/(p+1); e = data[0]
        for x in data[1:]: e = x*k + e*(1-k)
        return e
    # RSI
    g = sum(max(0, closes[i]-closes[i-1]) for i in range(-14,0))
    l = sum(max(0, closes[i-1]-closes[i]) for i in range(-14,0))
    rsi = 100 if l==0 else 100-(100/(1+(g/14)/(l/14)))
    # EMA
    ema20 = ema(closes[-20:],20)
    ema50 = ema(closes[-50:],50)
    ema200 = ema(closes[-100:],200)
    ma20 = sum(closes[-20:])/20
    std = math.sqrt(sum((x-ma20)**2 for x in closes[-20:])/20)
    bb_u, bb_l = ma20+2*std, ma20-2*std
    macd = ema(closes[-26:],12) - ema(closes[-26:],26)
    stoch = 100*(closes[-1]-min(lows[-14:]))/(max(highs[-14:])-min(lows[-14:])) if max(highs[-14:])!=min(lows[-14:]) else 50
    vwap = sum(c*v for c,v in zip(closes[-20:], vols[-20:]))/sum(vols[-20:])
    avg_vol = sum(vols
