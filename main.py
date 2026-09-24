import os, requests
W=os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK") or os.getenv("WEBHOOK")
def S(m):
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
    return 100-(100/(1+(g/14)/(l/14)))
def fetch_any(coin):
    for dom in ["data-api.binance.vision","api1.binance.com"]:
        j=G(f"https://{dom}/api/v3/klines?symbol={coin}USDT&interval=15m&limit=50")
        if j and len(j)>20:
            try:
                closes=[float(x[4]) for x in j]
                lows=[float(x[3]) for x in j]
                return closes,lows,"Binance",float(j[-1][4])
            except:
                pass
    return None
BLACKLIST={"USDT","USDC","FDUSD","BUSD","DAI","TUSD","USDP","USDE","TRY","BRL","PAXG","ARMB","STXB","AAPLB"}
S("V12.3 FIXED START")
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
            if base in BLACKLIST:
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
if j and 'symbols' in j:
    for s in j['symbols']:
        if s.get('quoteAsset')=='USDT' and s.get('status')=='TRADING':
            sym=s.get('symbol')
            if "BUSD" in sym:
                continue
            base=s.get('baseAsset')
            if base in BLACKLIST:
                continue
            all_coins.add(base)
tv_syms=set([x[0].replace("USDT","") for x in results])
to_scan=[c for c in all_coins if c not in tv_syms][:250]
for coin in to_scan:
    res=fetch_any(coin)
    if not res:
        continue
    closes,lows,src,price=res
    r=RSI(closes)
    ch=((closes[-1]-closes[0])/closes[0]*100) if closes[0]!=0 else 0
    sl=min(lows[-20:]) if len(lows)>=20 else price*0.98
    if r<50:
        results.append((f"{coin}USDT",r,price,sl,src,ch))
for pair in ["EURUSD","GBPUSD","XAUUSD","XAGUSD","AUDUSD","USDJPY"]:
    tv_fx=G("https://scanner.tradingview.com/forex/scan","POST",{"filter":[{"left":"name","operation":"match","right":pair}],"columns":["close","RSI","change"],"range":{"from":0,"to":10}})
    if tv_fx:
        if 'data' in tv_fx:
            if len(tv_fx['data'])>0:
                try:
                    v=tv_fx['data'][0]['d']
                    price=float(v[0] or 0)
                    rsi=float(v[1] or 50)
                    ch=float(v[2] or 0)
                    if price>0 and rsi<45:
                        results.append((pair,rsi,price,price*0.998,"FOREX",ch))
                except:
                    pass
if results:
    results=sorted(results, key=lambda x:x[1])
    scored=[]
    for sym,rsi,price,sup,src,change in results:
        score=0
        if rsi<25:
            score+=4
        elif rsi<30:
            score+=3
        elif rsi<35:
            score+=2
        if change<-5:
            score+=2
        scored.append((score,sym,rsi,price,sup,src,change))
    scored=sorted(scored, key=lambda x:x[0], reverse=True)
    S(f"SCAN REPORT Total {len(results)} | Top 5")
    S("--------------------")
    top5=scored[:5]
    for i in range(len(top5)):
        sc,sym,rsi,price,sup,src,change=top5[i]
        ps=round(price,6)
        ss=round(sup,6)
        tp1=round(price*1.04,6)
        tp2=round(price*1.08,6)
        acc=95 if sc>=5 else 90
        if "FOREX" in src:
            S(f"#{i+1} FOREX {acc}% | {sym} RSI {int(rsi)} Price {ps} SL {ss} TP1 {tp1} TP2 {tp2} BUY")
        else:
            S(f"#{i+1} LONG {acc}% | {sym} RSI {int(rsi)} Score {sc} Entry {ps} SL {ss} TP1 {tp1} TP2 {tp2} {src}")
    S("COMPLETE")
else:
    S("No signals")
