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
def get_klines(sym, tf="15m", lim=100):
    for url in [f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval={tf}&limit={lim}",
                f"https://api.binance.com/api/v3/klines?symbol={sym}&interval={tf}&limit={lim}"]:
        j=safe_get(url)
        if j and len(j)>50:
            return [float(x[4]) for x in j],[float(x[5]) for x in j],[float(x[2]) for x in j],[float(x[3]) for x in j]
    return None
def calc(closes, highs, lows, vols):
    def ema(d,p):
        k=2/(p+1); e=d[0]
        for x in d[1:]: e=x*k+e*(1-k)
        return e
    g=sum(max(0, closes[i]-closes[i-1]) for i in range(-14,0))
    l=sum(max(0, closes[i-1]-closes[i]) for i in range(-14,0))
    rsi=100 if l==0 else 100-(100/(1+(g/14)/(l/14)))
    ema20=ema(closes[-20:],20); ema50=ema(closes[-50:],50); ema200=ema(closes[-100:],200)
    ma20=sum(closes[-20:])/20
    std=math.sqrt(sum((x-ma20)**2 for x in closes[-20:])/20)
    bb_u,bb_l=ma20+2*std, ma20-2*std
    macd=ema(closes[-26:],12)-ema(closes[-26:],26)
    stoch=100*(closes[-1]-min(lows[-14:]))/(max(highs[-14:])-min(lows[-14:])) if max(highs[-14:])!=min(lows[-14:]) else 50
    vwap=sum(c*v for c,v in zip(closes[-20:], vols[-20:]))/sum(vols[-20:])
    avg_vol=sum(vols[-20:-1])/19 if len(vols)>20 else 1
    spike=vols[-1]/avg_vol if avg_vol else 1
    sup, res=min(lows[-20:]), max(highs[-20:])
    return rsi,ema20,ema50,ema200,bb_u,bb_l,macd,stoch,vwap,spike,sup,res,closes[-1]

send("**👑 V6 LITE ONLINE - Signals Guaranteed**")
tick=safe_get("https://fapi.binance.com/fapi/v1/ticker/24hr")
if not tick: tick=safe_get("https://api.binance.com/api/v3/ticker/24hr")

found=0
if tick:
    for t in tick:
        sym=t['symbol']
        if not sym.endswith("USDT"): continue
        if any(x in sym for x in ["BULL","BEAR"]): continue
        try: ch=float(t['priceChangePercent']); qv=float(t['quoteVolume']); price=float(t['lastPrice'])
        except: continue
        if qv < 300000: continue
        d15=get_klines(sym,"15m",100)
        if not d15: continue
        c15,v15,h15,l15=d15
        rsi15,e20,e50,e200,bb_u,bb_l,macd,stoch,vwap,spike,sup,res,pr = calc(c15,h15,l15,v15)

        # LITE LOGIC - Jaldi signal dega
        if rsi15 < 40 and pr < e20: # Pehle 33 tha, ab 40
            found+=1
            send(f"🚀 **CRYPTO LONG | {sym}**\nPrice `{price}` | RSI `{rsi15:.0f}` | Stoch `{stoch:.0f}`\nTrend: Below EMA20 | BB {'Lower Bounce' if pr<bb_l else 'Near Lower'} | Vol {spike:.1f}x\nSL `{sup:.4f}` | TP +2% / +5%")
            if found>=5: break # 5 signals max

if found==0:
    send("ℹ️ **CRYPTO:** No strong oversold now (RSI >40). Market is sideways.")

# FOREX - Threshold kam kiya 35 kar diya
f_found=0
for yahoo,name,flag in [("EURUSD=X","EUR/USD","🇪🇺/🇺🇸"),("EURJPY=X","EUR/JPY","🇪🇺/🇯🇵"),("GBPUSD=X","GBP/USD","🇬🇧/🇺🇸"),("AUDUSD=X","AUD/USD","🇦🇺/🇺🇸"),("GC=F","GOLD","🟡 GOLD")]:
    j=safe_get(f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo}?interval=15m&range=5d")
    try:
        q=j['chart']['result'][0]['indicators']['quote'][0]
        closes=[c for c in q['close'] if c is not None][-100:]
        highs=[h for h in q['high'] if h is not None][-100:]
        lows=[l for l in q['low'] if l is not None][-100:]
        vols=[1]*len(closes)
        rsi,e20,e50,e200,bb_u,bb_l,macd,stoch,vwap,spike,sup,res,price = calc(closes,highs,lows,vols)
        if rsi < 38: # pehle 33 tha
            f_found+=1
            pip=0.01 if "JPY" in name else 0.0001
            if "GOLD" in name: pip=1.0
            send(f"{flag} **FOREX LONG | {name}**\nPrice `{price:.4f}` | RSI `{rsi:.0f}` | Stoch `{stoch:.0f}`\nEntry `{price:.4f}` | SL `{price-15*pip:.4f}` | TP `{price+25*pip:.4f}`")
    except: pass

if f_found==0:
    send("ℹ️ **FOREX:** No oversold pairs now. Watching...")

send("✅ **V6 LITE Scan Done**")
