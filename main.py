import os, requests, time
W=os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK") or os.getenv("WEBHOOK")

def S(m):
    if not W:
        print(m)
        return
    try:
        requests.post(W, json={"content": m[:1900]}, timeout=20)
    except:
        print(m)

def G(u, method="GET", p=None):
    try:
        h={"User-Agent":"Mozilla/5.0"}
        if method=="POST":
            r=requests.post(u, json=p, timeout=20, headers=h)
        else:
            r=requests.get(u, timeout=15, headers=h)
        if r.status_code==200:
            return r.json()
        return None
    except:
        return None

def RSI(c):
    if len(c)<15:
        return 50
    g=sum(max(0,c[i]-c[i-1]) for i in range(-14,0))
    l=sum(max(0,c[i-1]-c[i]) for i in range(-14,0))
    if l==0:
        return 70
    rs=(g/14)/(l/14)
    return 100-(100/(1+rs))

def fetch_any(coin):
    for dom in ["data-api.binance.vision","api1.binance.com"]:
        j=G(f"https://{dom}/api/v3/klines?symbol={coin}USDT&interval=15m&limit=50")
        if j and isinstance(j,list) and len(j)>20:
            try:
                closes=[float(x[4]) for x in j]
                lows=[float(x[3]) for x in j]
                price=float(j[-1][4])
                return closes,lows,"Binance",price
            except:
                pass
    for url,src,ci,li in [(f"https://api.kucoin.com/api/v1/market/candles?type=15min&symbol={coin}-USDT","KuCoin",2,4),(f"https://api.bybit.com/v5/market/kline?category=spot&symbol={coin}USDT&interval=15&limit=50","Bybit",4,3),(f"https://www.okx.com/api/v5/market/candles?instId={coin}-USDT&bar=15m&limit=50","OKX",4,3)]:
        j=G(url)
        if not j:
            continue
        try:
            if 'data' in j:
                data=list(reversed(j['data']))
            elif 'result' in j and 'list' in j['result']:
                data=list(reversed(j['result']['list']))
            else:
                data=[]
            if len(data)>20:
                closes=[float(x[ci]) for x in data]
                lows=[float(x[li]) for x in data]
                return closes,lows,src,float(data[-1][ci])
        except:
            pass
    return None

BLACKLIST={"USDT","USDC","FDUSD","BUSD","DAI","TUSD","USDP","USDE","TRY","BRL","PAXG","ARMB","STXB","AAPLB","TSMB","KORUB"}

try:
    S("V12.3 STARTING - ALL EXCHANGE + FOREX")
    results=[]

    tv_all=G("https://scanner.tradingview.com/crypto/scan","POST",{"filter":[{"left":"exchange","operation":"equal","right":"BINANCE"},{"left":"name","operation":"match","right":"USDT"}],"columns":["close","RSI","change","volume"],"range":{"from":0,"to":1000},"sort":{"sortBy":"RSI","sortOrder":"asc"}})
    if tv_all and 'data' in tv_all:
        for d in tv_all['data']:
            try:
                v=d['d']
                sym=d['s'].replace("BINANCE:","")
                if not sym.endswith("USDT"):
                    continue
                if "BUSD" in sym:
                    continue
                base=sym.replace("USDT","")
                if base in BLACKLIST or base.endswith("B"):
                    continue
                c=float(v[0] or 0)
                r=float(v[1] or 50)
                ch=float(v[2] or 0)
                if c==0:
                    continue
                results.append((sym,r,c,c*0.98,"TV",ch))
            except:
                continue

    all_coins=set()
    j=G("https://data-api.binance.vision/api/v3/exchangeInfo")
    if not j:
        j=G("https://api.binance.com/api/v3/exchangeInfo")
    if j and 'symbols' in j:
        for s in j['symbols']:
            if s.get('quoteAsset')=='USDT' and s.get('status')=='TRADING':
                sym=s.get('symbol')
                if "BUSD" in sym:
                    continue
                base=s.get('baseAsset')
                if base in BLACKLIST or base.endswith("B") or len(base)<2:
                    continue
                all_coins.add(base)

    tv_syms=set([x[0].replace("USDT","") for x in results])
    to_scan=[c for c in all_coins if c not in tv_syms][:300]

    for coin in to_scan:
        res=fetch_any(coin)
        if not res:
            continue
        closes,lows,src,price=res
        r=RSI(closes)
        ch=((closes[-1]-closes[0])/closes[0]*100) if closes[0]!=0 else 0
        sl=min(lows[-20:]) if len(lows)>=20 else price*0.98
        if sl>=price*0.998:
            sl=price*0.98
        if r<50:
            results.append((f"{coin}USDT",r,price,sl,src,ch))

    # FOREX
    for pair in ["EURUSD","GBPUSD","USDJPY","XAUUSD","XAGUSD","AUDUSD"]:
        tv_fx=G("https://scanner.tradingview.com/forex/scan","POST",{"filter":[{"left":"name","operation":"match","right":pair}],"columns":["close","RSI","change"],"range":{"from":0,"to":10}})
        if tv_fx and 'data' in tv_fx and len(tv_fx['data'])>0:
