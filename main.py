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
            try: return [float(x[4]) for x in j],[float(x[3]) for x in j],"Binance",float(j[-1][4])
            except: pass
    for url,src,ci,li in [(f"https://api.kucoin.com/api/v1/market/candles?type=15min&symbol={coin}-USDT","KuCoin",2,4),(f"https://api.bybit.com/v5/market/kline?category=spot&symbol={coin}USDT&interval=15&limit=50","Bybit",4,3),(f"https://www.okx.com/api/v5/market/candles?instId={coin}-USDT&bar=15m&limit=50","OKX",4,3),(f"https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair={coin}_USDT&interval=15m&limit=50","Gate",2,3)]:
        j=G(url)
        if not j: continue
        try:
            data=list(reversed(j['data'])) if 'data' in j else list(reversed(j['result']['list'])) if 'result' in j and 'list' in j['result'] else list(reversed(j)) if isinstance(j,list) else []
            if len(data)>20: return [float(x[ci]) for x in data],[float(x[li]) for x in data],src,float(data[-1][ci])
        except: pass
    j=G(f"https://min-api.cryptocompare.com/data/v2/histominute?fsym={coin}&tsym=USD&limit=50&aggregate=15")
    if j and 'Data' in j and 'Data' in j['Data'] and len(j['Data']['Data'])>20:
        try: d=j['Data']['Data']; return [float(x['close']) for x in d],[float(x['low']) for x in d],"CryptoComp",float(d[-1]['close'])
        except: pass
    return None

BLACKLIST={"USDT","USDC","FDUSD","BUSD","DAI","TUSD","USDP","USDE","EUR","TRY","BRL","FDUSD","PAXG","GUSD"}
S("**👑 V11.5 ULTIMATE NO LIMIT + 100% PICKER ONLINE**")

# STEP 1: TRADINGVIEW 1000 COINS
tv_all=G("https://scanner.tradingview.com/crypto/scan","POST",{"filter":[{"left":"exchange","operation":"equal","right":"BINANCE"},{"left":"name","operation":"match","right":"USDT"}],"columns":["close","RSI","change","volume"],"range":{"from":0,"to":1000},"sort":{"sortBy":"RSI","sortOrder":"asc"}})
results=[]
if tv_all and 'data' in tv_all:
    for d in tv_all['data']:
        try:
            v=d['d']; sym=d['s'].replace("BINANCE:","")
            if not sym.endswith("USDT"): continue
            base=sym.replace("USDT","")
            if base in BLACKLIST: continue
            c=float(v[0] or 0); r=float(v[1] or 50); ch=float(v[2] or 0
