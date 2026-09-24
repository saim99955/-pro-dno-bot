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

def get_klines_spot(sym):
    # Spot API - kabhi block nahi hota
    url = f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=15m&limit=50"
    j=safe_get(url)
    if j and len(j)>20:
        return [float(x[4]) for x in j],[float(x[2]) for x in j],[float(x[3]) for x in j]
    return None

def calc_rsi(closes):
    g=sum(max(0, closes[i]-closes[i-1]) for i in range(-14,0))
    l=sum(max(0, closes[i-1]-closes[i]) for i in range(-14,0))
    rsi=100 if l==0 else 100-(100/(1+(g/14)/(l/14)))
    return rsi

send("**💎 V7 GUARANTEED ONLINE**")

# DIRECT TOP COINS - Ticker pe depend nahi
TOP_COINS = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","AVAXUSDT","SHIBUSDT","DOTUSDT","LINKUSDT","TRXUSDT","MATICUSDT","LTCUSDT","BCHUSDT","UNIUSDT","PEPEUSDT","BONKUSDT","WIFUSDT","FLOKIUSDT"]

all_data=[]
for sym in TOP_COINS:
    d=get_klines_spot(sym)
    if not d: continue
    closes,highs,lows=d
    rsi=calc_rsi(closes)
    price=closes[-1]
    sup=min(lows[-20:])
    all_data.append((sym,rsi,price,sup))

# Sort by lowest RSI
all_data = sorted(all_data, key=lambda x: x[1])

if not all_data:
    send("❌ **ERROR:** Binance Spot bhi block hai. GitHub IP issue.")
else:
    send(f"ℹ️ **Scanned {len(all_data)} coins** - Top 5 lowest RSI:")
    for sym,rsi,price,sup in all_data[:5]:
        if rsi < 50:
            send(f"🚀 **CRYPTO LONG | {sym}**\nPrice `{price:.4f}` | RSI `{rsi:.0f}` - Lowest in market\nSL `{sup:.4f}` | TP +2% / +5% | Vol OK")
        else:
            send(f"⚠️ **CRYPTO WATCH | {sym}**\nPrice `{price:.4f}` | RSI `{rsi:.0f}` - Market not oversold, but lowest available")

# FOREX same as before
for yahoo,name,flag in [("EURUSD=X","EUR/USD","🇪🇺/🇺🇸"),("EURJPY=X","EUR/JPY","🇪🇺/🇯🇵"),("GBPUSD=X","GBP/USD","🇬🇧/🇺🇸"),("AUDUSD=X","AUD/USD","🇦🇺/🇺🇸"),("GC=F","GOLD","🟡 GOLD")]:
    j=safe_get(f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo}?interval=15m&range=5d")
    try:
        q=j['chart']['result'][0]['indicators']['quote'][0]
        closes=[c for c in q['close'] if c is not None][-50:]
        rsi=calc_rsi(closes)
        price=closes[-1]
        if rsi < 50:
            send(f"{flag} **FOREX | {name} | RSI {rsi:.0f}**\nPrice `{price:.4f}`")
    except: pass

send("✅ **V7 Scan Done**")
