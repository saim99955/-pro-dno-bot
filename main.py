import os, requests, time
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK")
last_alert = {}
def send(m):
    try: requests.post(WEBHOOK, json={"content": m}, timeout=10)
    except: pass
def safe_get(u):
    try:
        r=requests.get(u, timeout=10)
        if r.status_code==200: return r.json()
    except: pass
    return None
def get_data(s):
    k=safe_get(f"https://fapi.binance.com/fapi/v1/klines?symbol={s}&interval=5m&limit=100")
    if not k or len(k)<50: return None
    k=k[:-1]
    closes=[float(x[4]) for x in k]; vols=[float(x[5]) for x in k]; price=closes[-1]
    g=sum(max(0, closes[i]-closes[i-1]) for i in range(-14,0)); l=sum(max(0, closes[i-1]-closes[i]) for i in range(-14,0))
    rsi=100 if l==0 else 100-(100/(1+(g/14)/(l/14)))
    avg=sum(vols[-20:-1])/19; spike=vols[-1]/avg if avg>0 else 1
    ls=safe_get(f"https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol={s}&period=5m&limit=1")
    long_p=50; short_p=50
    if ls and len(ls)>0: long_p=float(ls[0]['longAccount'])*100; short_p=float(ls[0]['shortAccount'])*100
    return price, rsi, spike, long_p, short_p
def scan():
    tick=safe_get("https://fapi.binance.com/fapi/v1/ticker/24hr")
    if not tick: return
    for t in tick:
        sym=t['symbol']
        if not sym.endswith("USDT"): continue
        if sym in last_alert and time.time()-last_alert[sym]<3600: continue
        try: ch=float(t['priceChangePercent']); qv=float(t['quoteVolume'])
        except: continue
        if qv<5000000: continue
        d=get_data(sym); time.sleep(0.3)
        if not d: continue
        price,rsi,spike,long_p,short_p=d
        if spike<1.8: continue
        if ch>8 and rsi>68 and long_p>60:
            sl=price*1.05; tp1=price*0.90; tp2=price*0.80
            send(f"🔴 **SHORT** | `{sym}` | Pump `+{ch:.1f}%` | RSI `{rsi:.0f}` | Vol x{spike:.1f}\nLongs {long_p:.0f}% vs Shorts {short_p:.0f}%\nENTRY {price}\nSL {sl:.2f} TP1 {tp1:.2f} TP2 {tp2:.2f}")
            last_alert[sym]=time.time()
        elif ch<-6 and rsi<38 and short_p>60:
            sl=price*0.94; tp1=price*1.10; tp2=price*1.22
            send(f"🟢 **LONG** | `{sym}` | Dump `{ch:.1f}%` | RSI `{rsi:.0f}` | Vol x{spike:.1f}\nLongs {long_p:.0f}% vs Shorts {short_p:.0f}%\nENTRY {price}\nSL {sl:.2f} TP1 {tp1:.2f} TP2 {tp2:.2f}")
            last_alert[sym]=time.time()
send("✅ BOT ONLINE - FREE GitHub")
while True:
    try: scan(); time.sleep(120)
    except: time.sleep(30)
