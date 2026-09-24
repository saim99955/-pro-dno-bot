import os, requests, time
WEBHOOK=os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK")

def send(m):
    try: requests.post(WEBHOOK, json={"content": m}, timeout=15)
    except: pass

def safe_get(u):
    try:
        r=requests.get(u, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code==200: return r.json()
    except Exception as e: print(e)
    return None

def get_klines(symbol, interval="5m", limit=100):
    j=safe_get(f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}")
    if not j or len(j)<50:
        # fallback to spot api
        j=safe_get(f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}")
    if not j or len(j)<50: return None
    closes=[float(x[4]) for x in j]
    vols=[float(x[5]) for x in j]
    highs=[float(x[2]) for x in j]
    lows=[float(x[3]) for x in j]
    price=closes[-1]
    g=sum(max(0, closes[i]-closes[i-1]) for i in range(-14,0))
    l=sum(max(0, closes[i-1]-closes[i]) for i in range(-14,0))
    rsi=100 if l==0 else 100-(100/(1+(g/14)/(l/14)))
    avg=sum(vols[-20:-1])/19 if len(vols)>20 else 1
    spike=vols[-1]/avg if avg else 1
    ma20=sum(closes[-20:])/20
    ma50=sum(closes[-50:])/50 if len(closes)>=50 else ma20
    return price, rsi, spike, ma20, ma50, highs, lows, closes

def get_ls_ratio(sym):
    ls=safe_get(f"https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol={sym}&period=5m&limit=1")
    try: return float(ls[0]['longAccount'])*100, float(ls[0]['shortAccount'])*100
    except: return 50,50

def get_forex(yahoo, name):
    j=safe_get(f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo}?interval=5m&range=1d")
    try:
        res=j['chart']['result'][0]
        closes=res['indicators']['quote'][0]['close']
        closes=[c for c in closes if c is not None][-100:]
        price=closes[-1]
        g=sum(max(0, closes[i]-closes[i-1]) for i in range(-14,0))
        l=sum(max(0, closes[i-1]-closes[i]) for i in range(-14,0))
        rsi=100 if l==0 else 100-(100/(1+(g/14)/(l/14)))
        return price, rsi
    except: return None

send("**V3 ULTRA ONLINE - USDT+USDC+FOREX+NEW COINS**")

# 1. CRYPTO SCAN - VOLUME FILTER KAM KAR DIYA
tick=safe_get("https://fapi.binance.com/fapi/v1/ticker/24hr")
if not tick:
    tick=safe_get("https://api.binance.com/api/v3/ticker/24hr")

if tick:
    for t in tick:
        sym=t['symbol']
        if not (sym.endswith("USDT") or sym.endswith("USDC")): continue
        if "BULL" in sym or "BEAR" in sym or "UP" in sym and len(sym)<10: continue
        try:
            ch=float(t['priceChangePercent'])
            qv=float(t['quoteVolume'])
            price_now=float(t['lastPrice'])
        except: continue
        if qv < 200000: continue # 1M se 200k kar diya

        d=get_klines(sym)
        if not d: continue
        price,rsi,spike,ma20,ma50,highs,lows,closes=d
        long_p,short_p=get_ls_ratio(sym)

        if ch > 50:
            send(f"**NEW PUMP +50%** | `{sym}` | +{ch:.1f}% | Vol ${qv/1000:.0f}k | RSI {rsi:.0f}")

        # YAHAN THRESHOLD KAM KAR DIYA TAKE SIGNALS AAYE
        if rsi < 35 and price < ma20: # pehle 25 tha
            send(f"🟢 **CRYPTO LONG | {sym} | RSI {rsi:.0f} OVERSOLD** | Price {price} | LS {long_p:.0f}/{short_p:.0f}")

        if rsi > 70 and price > ma20:
            send(f"🔴 **CRYPTO SHORT | {sym} | RSI {rsi:.0f} OVERBOUGHT** | Price {price}")

# 2. FOREX
forex_list=[("EURJPY=X","EUR/JPY"),("EURUSD=X","EUR/USD"),("AUDUSD=X","AUD/USD"),("GBPUSD=X","GBP/USD"),("XAUUSD=X","GOLD")]
for yahoo,name in forex_list:
    res=get_forex(yahoo,name)
    if not res: continue
    price,rsi=res
    if rsi < 25:
        send(f"🟢 **FOREX/GOLD LONG | {name} | RSI {rsi:.0f} OVERSOLD** | Price {price}")
    elif rsi < 32:
        send(f"⚠️ **FOREX WATCH | {name} | RSI {rsi:.0f}** | Price {price}")

send("✅ **V3 ULTRA Scan Complete - Next scan in 1 hour**")
