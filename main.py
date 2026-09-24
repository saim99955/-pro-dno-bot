import os, requests, math
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK")
def send(m):
    try: requests.post(WEBHOOK, json={"content": m}, timeout=15)
    except: pass
def safe_get(u):
    try:
        r=requests.get(u, timeout=12, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code==200: return r.json()
    except: pass
    return None
def get_klines(sym, tf="15m", lim=80):
    for url in [f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval={tf}&limit={lim}",
                f"https://api.binance.com/api/v3/klines?symbol={sym}&interval={tf}&limit={lim}"]:
        j=safe_get(url)
        if j and len(j)>30:
            return [float(x[4]) for x in j],[float(x[5]) for x in j],[float(x[2]) for x in j],[float(x[3]) for x in j]
    return None
def calc(closes, highs, lows, vols):
    g=sum(max(0, closes[i]-closes[i-1]) for i in range(-14,0))
    l=sum(max(0, closes[i-1]-closes[i]) for i in range(-14,0))
    rsi=100 if l==0 else 100-(100/(1+(g/14)/(l/14)))
    return rsi, min(lows[-20:]), max(highs[-20:]), closes[-1]

send("**💎 V6 PRO MAX ONLINE - USDT+USDC+ALL**")
tick=safe_get("https://fapi.binance.com/fapi/v1/ticker/24hr")
if not tick: tick=safe_get("https://api.binance.com/api/v3/ticker/24hr")

all_coins=[]
if tick:
    for t in tick:
        sym=t['symbol']
        # Ab USDT + USDC dono
        if not (sym.endswith("USDT") or sym.endswith("USDC")): continue
        if any(x in sym for x in ["BULL","BEAR","UP","DOWN","EUR","GBP"]): continue
        try: ch=float(t['priceChangePercent']); qv=float(t['quoteVolume']); price=float(t['lastPrice'])
        except: continue
        if qv < 150000: continue # volume filter kam kiya 800k se 150k
        d=get_klines(sym,"15m",80)
        if not d: continue
        c,v,h,l=d
        rsi,sup,res,pr = calc(c,h,l,v)
        all_coins.append((sym,rsi,ch,qv,price,sup))

    # Sab se zyada oversold 5 coins nikalo - chahe RSI 50 bhi ho
    all_coins = sorted(all_coins, key=lambda x: x[1])[:5]
    for sym,rsi,ch,qv,price,sup in all_coins:
        if rsi < 45:
            send(f"🚀 **CRYPTO LONG | {sym}**\nPrice `{price}` | RSI `{rsi:.0f}` | Change `{ch:.1f}%`\nSL `{sup:.4f}` | TP +2% / +5% - BEST PICK")
        else:
            send(f"⚠️ **CRYPTO WATCH | {sym}**\nPrice `{price}` | RSI `{rsi:.0f}` (Lowest in market) | Change `{ch:.1f}%`\nWait for dip <45")

# FOREX same
for yahoo,name,flag in [("EURUSD=X","EUR/USD","🇪🇺/🇺🇸"),("EURJPY=X","EUR/JPY","🇪🇺/🇯🇵"),("GBPUSD=X","GBP/USD","🇬🇧/🇺🇸"),("AUDUSD=X","AUD/USD","🇦🇺/🇺🇸"),("GC=F","GOLD","🟡 GOLD")]:
    j=safe_get(f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo}?interval=15m&range=5d")
    try:
        q=j['chart']['result'][0]['indicators']['quote'][0]
        closes=[c for c in q['close'] if c is not None][-80:]
        highs=[h for h in q['high'] if h is not None][-80:]
        lows=[l for l in q['low'] if l is not None][-80:]
        vols=[1]*len(closes)
        rsi,sup,res,price = calc(closes,highs,lows,vols)
        pip=0.01 if "JPY" in name else 0.0001
        if "GOLD" in name: pip=1.0
        if rsi < 50:
            send(f"{flag} **FOREX | {name} | RSI {rsi:.0f}**\nPrice `{price:.4f}` | Entry `{price:.4f}` | SL `{price-15*pip:.4f}` | TP `{price+25*pip:.4f}`")
    except: pass

send("✅ **V6 PRO MAX Scan Done**")
