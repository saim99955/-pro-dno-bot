import os, requests, time
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK")

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
    if not j or len(j)<50: return None
    j=j[:-1]
    closes=[float(x[4]) for x in j]
    vols=[float(x[5]) for x in j]
    highs=[float(x[2]) for x in j]
    lows=[float(x[3]) for x in j]
    price=closes[-1]
    # RSI 14
    g=sum(max(0, closes[i]-closes[i-1]) for i in range(-14,0))
    l=sum(max(0, closes[i-1]-closes[i]) for i in range(-14,0))
    rsi=100 if l==0 else 100-(100/(1+(g/14)/(l/14)))
    # Vol spike
    avg=sum(vols[-20:-1])/19 if len(vols)>20 else 1
    spike=vols[-1]/avg if avg>0 else 1
    # MA check
    ma20=sum(closes[-20:])/20
    ma50=sum(closes[-50:])/50
    return price, rsi, spike, ma20, ma50, highs, lows, closes

def get_ls_ratio(sym):
    ls=safe_get(f"https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol={sym}&period=5m&limit=1")
    try: return float(ls[0]['longAccount'])*100, float(ls[0]['shortAccount'])*100
    except: return 50,50

def get_forex(yahoo, name):
    j=safe_get(f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo}?interval=5m&range=2d")
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

send("✅ **V3 ULTRA ONLINE - USDT+USDC+FOREX+NEW COINS**")

# 1. CRYPTO SCAN - USDT & USDC
tick=safe_get("https://fapi.binance.com/fapi/v1/ticker/24hr")
if tick:
    for t in tick:
        sym=t['symbol']
        if not (sym.endswith("USDT") or sym.endswith("USDC")): continue
        if "BULL" in sym or "BEAR" in sym or "UP" in sym and len(sym)<10: continue

        try:
            ch=float(t['priceChangePercent'])
            qv=float(t['quoteVolume'])
            high=float(t['highPrice'])
            low=float(t['lowPrice'])
            price_now=float(t['lastPrice'])
        except: continue

        if qv < 1000000: continue # 1M volume minimum

        d=get_klines(sym)
        if not d: continue
        price,rsi,spike,ma20,ma50,highs,lows,closes=d
        long_p,short_p=get_ls_ratio(sym)

        # === CHECK 1: NEW COIN +50% PUMP ===
        if ch >= 50:
            send(f"🚀 **NEW PUMP +50%** | `{sym}` | `+{ch:.1f}%` | Vol ${qv/1e6:.1f}M x{spike:.1f} | RSI {rsi:.0f}\nPrice {price_now} | High {high} Low {low}\nLong {long_p:.0f}% Short {short_p:.0f}%\n⚠️ New listing pump - high risk!")

        # === CHECK 2: ULTRA PUMP +20% ===
        elif ch >= 20 and spike>=2.0 and rsi>=70:
            send(f"🔴 **ULTRA SHORT SETUP** | `{sym}` | Pump `+{ch:.1f}%` | RSI `{rsi:.0f}` | Vol x{spike:.1f}\nLongs {long_p:.0f}% (crowded) | Price > MA20 {price>ma20}\nENTRY {price}\nSL {price*1.08:.4f} TP1 {price*0.85:.4f}")

        # === CHECK 3: DUMP -15% ===
        elif ch <= -15 and rsi<=35:
            send(f"🟢 **ULTRA LONG BOUNCE** | `{sym}` | Dump `{ch:.1f}%` | RSI `{rsi:.0f}` | Vol x{spike:.1f}\nShorts {short_p:.0f}% (crowded)\nENTRY {price}\nSL {price*0.90:.4f} TP1 {price*1.15:.4f}")

        # === CHECK 4: NORMAL PRO SIGNALS (low filter) ===
        elif ch>=6 and rsi>=62 and spike>=1.5:
            send(f"🔴 **PRO SHORT** | `{sym}` | `+{ch:.1f}%` | RSI {rsi:.0f} | Vol x{spike:.1f} | L/S {long_p:.0f}/{short_p:.0f}%")
        elif ch<=-4 and rsi<=38 and spike>=1.5:
            send(f"🟢 **PRO LONG** | `{sym}` | `{ch:.1f}%` | RSI {rsi:.0f} | Vol x{spike:.1f} | L/S {long_p:.0f}/{short_p:.0f}%")

        time.sleep(0.15)

# 2. FOREX + GOLD SCAN
forex_list=[("EURUSD=X","EUR/USD"),("GBPUSD=X","GBP/USD"),("USDJPY=X","USD/JPY"),("AUDUSD=X","AUD/USD"),("EURJPY=X","EUR/JPY"),("XAUUSD=X","GOLD"),("XAGUSD=X","SILVER")]
for yahoo,name in forex_list:
    f=get_forex(yahoo,name)
    if not f: continue
    price,rsi=f
    if rsi>=75:
        send(f"🔴 **FOREX/GOLD SHORT** | `{name}` | RSI `{rsi:.0f}` OVERBOUGHT | Price {price}")
    elif rsi<=25:
        send(f"🟢 **FOREX/GOLD LONG** | `{name}` | RSI `{rsi:.0f}` OVERSOLD | Price {price}")
    elif rsi>=70 or rsi<=30:
        send(f"⚠️ **FOREX WATCH** | `{name}` | RSI `{rsi:.0f}` | Price {price}")

send("✅ **V3 ULTRA Scan Complete - Next scan in 1 hour**")
