import os, requests, math
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK")

def send(m):
    try:
        requests.post(WEBHOOK, json={"content": m}, timeout=15)
    except:
        pass

def safe_get(u):
    try:
        r = requests.get(u, timeout=12, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def get_klines(sym, tf="15m", lim=200):
    urls = [
        f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval={tf}&limit={lim}",
        f"https://api.binance.com/api/v3/klines?symbol={sym}&interval={tf}&limit={lim}"
    ]
    for url in urls:
        j = safe_get(url)
        if j and len(j) > 50:
            closes = [float(x[4]) for x in j]
            vols = [float(x[5]) for x in j]
            highs = [float(x[2]) for x in j]
            lows = [float(x[3]) for x in j]
            return closes, vols, highs, lows
    return None

def calc(closes, highs, lows, vols):
    def ema(data, p):
        k = 2/(p+1)
        e = data[0]
        for x in data[1:]:
            e = x*k + e*(1-k)
        return e

    g = sum(max(0, closes[i]-closes[i-1]) for i in range(-14,0))
    l = sum(max(0, closes[i-1]-closes[i]) for i in range(-14,0))
    rsi = 100 if l==0 else 100-(100/(1+(g/14)/(l/14)))

    ema20 = ema(closes[-20:],20)
    ema50 = ema(closes[-50:],50)
    ema200 = ema(closes[-100:],200)
    ma20 = sum(closes[-20:])/20
    std = math.sqrt(sum((x-ma20)**2 for x in closes[-20:])/20)
    bb_u = ma20+2*std
    bb_l = ma20-2*std
    macd = ema(closes[-26:],12) - ema(closes[-26:],26)
    lowest = min(lows[-14:])
    highest = max(highs[-14:])
    stoch = 100*(closes[-1]-lowest)/(highest-lowest) if highest!=lowest else 50
    vwap = sum(c*v for c,v in zip(closes[-20:], vols[-20:]))/sum(vols[-20:])
    avg_vol = sum(vols[-20:-1])/19 if len(vols)>20 else 1
    spike = vols[-1]/avg_vol if avg_vol else 1
    sup = min(lows[-20:])
    res = max(highs[-20:])
    fvg = highs[-3] < lows[-1]
    ob = lows[-2] == min(lows[-5:])
    liq_sweep = closes[-1] <= sup*1.002
    return rsi, ema20, ema50, ema200, bb_u, bb_l, macd, stoch, vwap, spike, sup, res, fvg, ob, liq_sweep, closes[-1]

def get_oi_funding(sym):
    try:
        oi = safe_get(f"https://fapi.binance.com/fapi/v1/openInterest?symbol={sym}")
        fund = safe_get(f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={sym}")
        return float(oi['openInterest']), float(fund['lastFundingRate'])*100
    except:
        return 0,0

ACCOUNT = 1000
send("**👑 V6 FINAL BOSS ONLINE**")

tick = safe_get("https://fapi.binance.com/fapi/v1/ticker/24hr")
if not tick:
    tick = safe_get("https://api.binance.com/api/v3/ticker/24hr")

if tick:
    for t in tick:
        sym = t['symbol']
        if not sym.endswith("USDT"): continue
        if any(x in sym for x in ["BULL","BEAR","UP","DOWN"]): continue
        try:
            ch = float(t['priceChangePercent'])
            qv = float(t['quoteVolume'])
            price = float(t['lastPrice'])
        except:
            continue
        if qv < 500000: continue

        d15 = get_klines(sym,"15m",200)
        d1h = get_klines(sym,"1h",200)
        if not d15 or not d1h: continue
        c15,v15,h15,l15 = d15
        c1h,v1h,h1h,l1h = d1h

        rsi15,e20_15,e50_15,e200_15,bb_u15,bb_l15,macd15,stoch15,vwap15,spike15,sup15,res15,fvg15,ob15,liq15,pr15 = calc(c15,h15,l15,v15)
        rsi1h,e20_1h,e50_1h,e200_1h,_,_,macd1h,_,_,_,_,_,_,_,_,_ = calc(c1h,h1h,l1h,v1h)

        conf = 0
        if rsi15<33: conf+=20
        if rsi1h<42: conf+=15
        if pr15 < bb_l15: conf+=15
        if fvg15: conf+=10
        if ob15: conf+=15
        if liq15: conf+=10
        if spike15>2.5: conf+=10
        if macd15>0 and macd1h>0: conf+=15

        if conf >= 70:
            oi, fund = get_oi_funding(sym)
            lot = round((ACCOUNT*0.01)/(price*0.009),3)
            send(f"👑 **V6 GOD LONG | {sym}**\n**Confidence {conf}%** | Price {price} | RSI {rsi15:.0f} | Vol {spike15:.1f}x\nSMC: {'FVG' if fvg15 else ''} {'OB' if ob15 else ''} {'LIQ' if liq15 else ''}\nSL {sup15:.4f} | TP +2% / +5% | Lot {lot}")

# FOREX SEPARATE TEMPLATE
for yahoo,name,flag in [("EURUSD=X","EUR/USD","🇪🇺/🇺🇸"),("EURJPY=X","EUR/JPY","🇪🇺/🇯🇵"),("GBPUSD=X","GBP/USD","🇬🇧/🇺🇸"),("GC=F","GOLD","🟡")]:
    j = safe_get(f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo}?interval=15m&range=5d")
    try:
        q = j['chart']['result'][0]['indicators']['quote'][0]
        closes = [c for c in q['close'] if c is not None][-100:]
        highs = [h for h in q['high'] if h is not None][-100:]
        lows = [l for l in q['low'] if l is not None][-100:]
        vols = [1]*len(closes)
        rsi,e20,e50,e200,bb_u,bb_l,macd,stoch,vwap,spike,sup,res,fvg,ob,liq,price = calc(closes,highs,lows,vols)
        conf=0
        if rsi<33: conf+=30
        if price<bb_l: conf+=30
        if fvg: conf+=20
        if ob: conf+=20
        if conf>=70:
            pip = 0.01 if "JPY" in name else 0.0001
            if "GOLD" in name: pip=1.0
            send(f"👑 {flag} **V6 FOREX GOD | {name} | CONF {conf}%**\nPrice {price:.4f} | RSI {rsi:.0f}\nEntry {price:.4f} | SL {price-15*pip:.4f} | TP +25/+50 pips")
    except:
        pass

send("✅ **V6 Scan Done**")
