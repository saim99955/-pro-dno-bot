import os, requests, time
W=os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK") or os.getenv("WEBHOOK")
def S(m):
    if not W: print(m); return
    try: requests.post(W, json={"content": m[:1900]}, timeout=20)
    except: print(m)
def G(u, method="GET", p=None):
    try:
        h={"User-Agent":"Mozilla/5.0"}
        r=requests.post(u, json=p, timeout=20, headers=h) if method=="POST" else requests.get(u, timeout=15, headers=h)
        return r.json() if r.status_code==200 else None
    except: return None
def RSI(c):
    if len(c)<15: return 50
    g=sum(max(0,c[i]-c[i-1]) for i in range(-14,0)); l=sum(max(0,c[i-1]-c[i]) for i in range(-14,0))
    return 70 if l==0 else 100-(100/(1+(g/14)/(l/14)))

def fetch_any(coin):
    for dom in ["data-api.binance.vision","api1.binance.com","api2.binance.com"]:
        j=G(f"https://{dom}/api/v3/klines?symbol={coin}USDT&interval=15m&limit=50")
        if j and isinstance(j,list) and len(j)>20:
            try: return [float(x[4]) for x in j],[float(x[3]) for x in j],"Binance"
            except: pass
    for url,src,ci,li in [
        (f"https://api.kucoin.com/api/v1/market/candles?type=15min&symbol={coin}-USDT","KuCoin",2,4),
        (f"https://api.bybit.com/v5/market/kline?category=spot&symbol={coin}USDT&interval=15&limit=50","Bybit",4,3),
        (f"https://www.okx.com/api/v5/market/candles?instId={coin}-USDT&bar=15m&limit=50","OKX",4,3),
        (f"https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair={coin}_USDT&interval=15m&limit=50","Gate",2,3)
    ]:
        j=G(url)
        if not j: continue
        try:
            data=list(reversed(j['data'])) if 'data' in j else list(reversed(j['result']['list'])) if 'result' in j and 'list' in j['result'] else list(reversed(j)) if isinstance(j,list) else []
            if len(data)>20: return [float(x[ci]) for x in data],[float(x[li]) for x in data],src
        except: pass
    j=G(f"https://min-api.cryptocompare.com/data/v2/histominute?fsym={coin}&tsym=USD&limit=50&aggregate=15")
    if j and 'Data' in j and 'Data' in j['Data'] and len(j['Data']['Data'])>20:
        try: d=j['Data']['Data']; return [float(x['close']) for x in d],[float(x['low']) for x in d],"CryptoComp"
        except: pass
    return None

S("**👑 V11.3 ULTIMATE NO LIMIT - ALL EXCHANGES + ALL COINS SCAN START**")

# STEP 1: TRADINGVIEW FULL - 1000 coins tak
tv_all = G("https://scanner.tradingview.com/crypto/scan","POST",{
    "filter":[{"left":"exchange","operation":"equal","right":"BINANCE"},{"left":"name","operation":"match","right":"USDT"}],
    "columns":["close","RSI","change","market_cap","volume","name"],
    "range":{"from":0,"to":1000},
    "sort":{"sortBy":"market_cap","sortOrder":"desc"}
})
results=[]
if tv_all and 'data' in tv_all:
    for d in tv_all['data']:
        try:
            v=d['d']; sym=d['s'].replace("BINANCE:","")
            if not sym.endswith("USDT"): continue
            c=float(v[0] or 0); r=float(v[1] or 50); ch=float(v[2] or 0)
            if c==0: continue
            results.append((sym,r,c,c*0.99,"TradingView-1000",ch,50))
        except: continue
    S(f"✅ TradingView ALL: {len(results)} coins")

# STEP 2: ALL EXCHANGES - Binance ke saare USDT pairs nikalo
S("🔍 Fetching ALL symbols from exchanges...")
all_coins=set()
# Binance ALL
j=G("https://data-api.binance.vision/api/v3/exchangeInfo")
if not j: j=G("https://api.binance.com/api/v3/exchangeInfo")
if j and 'symbols' in j:
    for s in j['symbols']:
        if s.get('quoteAsset')=='USDT' and s.get('status')=='TRADING':
            all_coins.add(s.get('baseAsset'))
S(f"Binance ALL USDT pairs: {len(all_coins)}")

# KuCoin ALL
j=G("https://api.kucoin.com/api/v1/symbols")
if j and 'data' in j:
    for s in j['data']:
        if s['quoteCurrency']=='USDT' and s['enableTrading']: all_coins.add(s['baseCurrency'])
S(f"Total unique coins after ALL exchanges: {len(all_coins)}")

# STEP 3: AB HAR COIN KO SCAN KARO - NO LIMIT
# TradingView me jo nahi mile unko exchanges se
tv_syms=set([x[0].replace("USDT","") for x in
