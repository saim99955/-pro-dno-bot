import requests, time

# ===== APNA WEBHOOK YAHAN DALO =====
W = "YAHAN APNA DISCORD WEBHOOK LINK DALO"
# ===================================

def S(m):
    print(m)
    try:
        requests.post(W, json={"content": m[:1900]}, timeout=10)
    except: pass

def G(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code==200:
            return r.json()
    except: return None
    return None

def GET_SIGNAL():
    # Binance trending
    data = G("https://data-api.binance.vision/api/v3/ticker/24hr")
    if not data:
        data = G("https://api.binance.com/api/v3/ticker/24hr")
    if not data: return []

    signals=[]
    for t in data:
        sym=t.get('symbol','')
        if not sym.endswith('USDT'): continue
        if any(x in sym for x in ['BUSD','USDC','FDUSD','BULL','BEAR']): continue

        ch = float(t.get('priceChangePercent',0))
        vol = float(t.get('quoteVolume',0))
        price = float(t.get('lastPrice',0))

        if vol < 10000000: continue
        if ch < 10 or ch > 60: continue

        # Klines for MA
        kl = G(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval=15m&limit=100")
        if not kl:
            kl = G(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=15m&limit=100")
        if not kl or len(kl)<99: continue

        closes=[float(x[4]) for x in kl]
        ma7 = sum(closes[-7:])/7
        ma25 = sum(closes[-25:])/25
        ma99 = sum(closes[-99:])/99

        # Signal condition - jaise BROCCOLI me hai
        # Price MA7 ke upar, MA7 MA25 ke upar, MA25 MA99 ke upar = Strong Uptrend
        if price < ma7: continue
        if ma7 < ma25: continue
        if ma25 < ma99: continue
        # 15m green candle
        if closes[-1] < closes[-2]: continue

        # Entry, SL, TP calculation - jaise aapne kiya
        entry = price
        sl = ma7 * 0.99 # MA7 se 1% neeche - BROCCOLI me 0.03218 tha
        tp1 = entry * 1.06 # +6%
        tp2 = entry * 1.10 # +10%
        tp3 = entry * 1.15 # +15%

        lev = "5x-10x"
        if ch > 30: lev = "5x Only (High Pump)"

        rr = (tp1-entry)/(entry-sl) if entry>sl else 0

        if rr < 1.5: continue

        signals.append((ch, sym, entry, sl, tp1, tp2, tp3, ma7, ma25, ma99, vol, lev))

    return sorted(signals, key=lambda x: x[0], reverse=True)[:3]

# ===== RUN =====
S(f"🔍 **SCANNING TRENDING SIGNALS {time.strftime('%H:%M')}**")

sigs = GET_SIGNAL()

if not sigs:
    S("⚠️ Abhi koi perfect setup nahi - MA7 ke upar koi trending coin nahi")
else:
    for ch,sym,entry,sl,tp1,tp2,tp3,ma7,ma25,ma99,vol,lev in sigs:
        msg = f"""
🚀 **{sym} Perp | +{round(ch,1)}%**
━━━━━━━━━━━━━━
💰 **Entry:** {entry}
🛑 **SL:** {round(sl,6)} (MA7 {round(ma7,6)})
🎯 **TP1:** {round(tp1,6)} (+6%)
🎯 **TP2:** {round(tp2,6)} (+10%)
🎯 **TP3:** {round(tp3,6)} (+15%)
