import os, requests, json
from datetime import datetime

W = os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK") or os.getenv("WEBHOOK")
BAL_FILE = "paper_balance.json"

# ===== $300 CAPITAL FINAL SETTINGS =====
TOTAL_CAPITAL = 300.0
TRADE_SIZE = 100.0 # 3 trades x $100 = $300
RISK_PER_TRADE = 0.02
# =======================================

def S(m):
    if not W:
        print(m)
        return
    try:
        requests.post(W, json={"content": m[:1900]}, timeout=20)
    except:
        print(m)

def G(url):
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None

def RSI(closes):
    if len(closes) < 15:
        return 50
    g = 0
    l = 0
    for i in range(1, 15):
        diff = closes[-i] - closes[-i-1]
        if diff > 0:
            g += diff
        else:
            l += abs(diff)
    if l == 0:
        return 70
    rs = (g / 14) / (l / 14)
    return 100 - (100 / (1 + rs))

def BACKTEST(closes, highs):
    wins = 0
    total = 0
    if len(closes) < 100:
        return 0, 0
    for i in range(15, len(closes) - 21):
        c = closes[i-14:i+1]
        r = RSI(c)
        if r < 30:
            total += 1
            ent = closes[i]
            tp1 = ent * 1.04
            fut = highs[i+1:i+21]
            if any(h >= tp1 for h in fut):
                wins += 1
    wr = (wins / total * 100) if total > 0 else 0
    return wr, total

def GET_LEV(rsi, vola, wr):
    if rsi < 18 and vola < 0.025 and wr > 70:
        return 10, "STRONG BOTTOM"
    elif rsi < 22 and vola < 0.04 and wr > 65:
        return 5, "GOOD SETUP"
    elif rsi < 28:
        return 3, "NORMAL"
    else:
        return 2, "RISKY"

def LOAD():
    try:
        if os.path.exists(BAL_FILE):
            with open(BAL_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {"balance": TOTAL_CAPITAL, "positions": {}, "trades": 0, "profit": 0.0, "wins": 0, "loss": 0}

def SAVE(d):
    try:
        with open(BAL_FILE, 'w') as f:
            json.dump(d, f)
    except:
        pass

BLACKLIST = {"BUSD","USDC","FDUSD","USDT","DAI","TUSD","USDP","EUR","BRL","TRY","PAXG","MARSCOIN","LOTI","XNO","JST","CATI","PHA","SYN","AUDIO","TRX","REQ","1INCH","BULL","BEAR","UP","DOWN"}

S(f"**V15.2 FINAL $300 | RISK+PAPER+BACKTEST+LEVERAGE START**")

try:
    data = LOAD()
    bal = float(data.get("balance", TOTAL_CAPITAL))
    pos = data.get("positions", {})

    # ===== 1. PAPER TRADING - OLD POSITIONS CHECK =====
    for sym in list(pos.keys()):
        p = pos[sym]
        tk = G(f"https://data-api.binance.vision/api/v3/ticker/price?symbol={sym}")
        if not tk:
            tk = G(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}")
        if not tk or "price" not in tk:
            continue
        try:
            cur = float(tk["price"])
            entry = float(p["entry"])
            sl = float(p["sl"])
            tp1 = float(p["tp1"])
            tp2 = float(p["tp2"])
            qty = float(p["qty"])
            lev = int(p.get("lev", 3))
            invested = float(p.get("invested", 100))

            if cur >= tp2:
                profit = (tp2 - entry) * qty * lev
                bal = bal + invested + profit
                S(f"✅ **TP2 HIT +{8*lev}%** | {sym} Entry {entry} -> {tp2} | Profit **${round(profit,2)}** | Bal ${round(bal,2)}")
                data["profit"] = float(data.get("profit", 0)) + profit
                data["trades"] = int(data.get("trades", 0)) + 1
                data["wins"] = int(data.get("wins", 0)) + 1
                del pos[sym]
            elif cur >= tp1 and p.get("hit1") is None:
                profit = (tp1 - entry) * (qty / 2) * lev
                bal = bal + profit
                p["sl"] = entry
                p["hit1"] = True
                p["qty"] = qty / 2
                S(f"🎯 **TP1 HIT +{4*lev}%** | {sym} Half sold Profit ${round(profit,2)} SL->Entry Bal ${round(bal,2)}")
                data["profit"] = float(data.get("profit", 0)) + profit
            elif cur <= sl:
                loss = (cur - entry) * qty * lev
                bal = bal + invested + loss
                perc = round(abs(cur-entry)/entry*100*lev, 1)
                S(f"❌ **SL HIT -{perc}%** | {sym} Entry {entry} -> {cur} | Loss ${round(loss,2)} | Bal ${round(bal,2)}")
                data["profit"] = float(data.get("profit", 0)) + loss
                data["trades"] = int(data.get("trades", 0)) + 1
                data["loss"] = int(data.get("loss", 0)) + 1
                del pos[sym]
        except Exception as e:
            continue

    # ===== 2. SCAN BINANCE =====
    info = G("https://data-api.binance.vision/api/v3/exchangeInfo")
    if not info:
        info = G("https://api.binance.com/api/v3/exchangeInfo")

    coins = []
    if info and 'symbols' in info:
        for s in info['symbols']:
            if s.get('quoteAsset') == 'USDT' and s.get('status') == 'TRADING':
                base = s.get('baseAsset')
                sym = s.get('symbol')
                if base in BLACKLIST:
                    continue
                if len(base) < 2 or len(base) > 8:
                    continue
                if "BULL" in sym or "BEAR" in sym:
                    continue
                coins.append(base)

    results = []
    moon = []

    for coin in coins[:150]:
        klines = G(f"https://data-api.binance.vision/api/v3/klines?symbol={coin}USDT&interval=15m&limit=100")
        if not klines or len(klines) < 60:
            continue
        try:
            closes = [float(x[4]) for x in klines]
            highs = [float(x[2]) for x in klines]
            lows = [float(x[3]) for x in klines]
            vols = [float(x[5]) for x in klines]
            price = closes[-1]

            vol_usd = (sum(vols[-20:]) / 20) * price
            if vol_usd < 250000:
                continue

            rsi = RSI(closes)
            vola = (max(highs[-20:]) - min(lows[-20:])) / price if price!= 0 else 0
            low_30d = min(lows)
            high_30d = max(highs)
            pot_x = (high_30d / price) if price!= 0 else 0
            dist_low = ((price - low_30d) / low_30d * 100) if low_30d!= 0 else 100

            if rsi < 35 and rsi > 5:
                sup = min(lows[-20:])
                if sup >= price * 0.98:
                    sup = price * 0.96
                wr, tot = BACKTEST(closes, highs)
                lev, lev_reason = GET_LEV(rsi, vola, wr)
                results.append((coin+"USDT", rsi, price, sup, wr, tot, vola, lev, lev_reason))

            if dist_low < 12 and rsi < 26 and pot_x >= 2.0 and pot_x <= 5.0:
                wr, tot = BACKTEST(closes, highs)
                if wr > 60 and tot >= 5:
                    moon.append((coin+"USDT", rsi, price, low_30d, pot_x, wr, tot))

        except:
            continue

    # ===== 3. REPORT =====
    total_profit = float(data.get("profit", 0))
    winrate_paper = (data.get("wins",0) / data.get("trades",1) * 100) if data.get("trades",0) > 0 else 0

    S(f"💰 BAL **${round(bal,2)}/${TOTAL_CAPITAL}** | PnL **${round(total_profit,2)}** | Pos {len(pos)}/3 | Win {round(winrate_paper,1)}%")
    S(f"📊 Scan {len(coins[:150])} | Low RSI {len(results)} | 1X-5X {len(moon)} | Trades {data.get('trades',0)}")
    S("--------------------")

    # ===== 4. NEW BUY - $300 RISK MANAGEMENT =====
    if results:
        results_sorted = sorted(results, key=lambda x: (x[1], -x[4]))

        count = 0
        for item in results_sorted:
            if count >= 3:
                break
            sym, rsi, price, sup, wr, tot, vola, lev, lev_reason = item

            if sym in pos:
                continue
            if bal < 95:
                S(f"⚠️ Balance low ${round(bal,2)} - Need $100 for trade")
                break
            if len(pos) >= 3:
                S(f"⚠️ Max 3 positions for $300 capital - Already {len(pos)} open")
                break

            invest = TRADE_SIZE
            if bal < TRADE_SIZE:
                invest = bal * 0.95

            qty = invest / price
            bal = bal - invest

            pos[sym] = {
                "entry": price,
                "sl": sup,
                "tp1": price * 1.04,
                "tp2": price * 1.08,
                "qty": qty,
                "invested": invest,
                "lev": lev,
                "time": str(datetime.now())[:19]
            }

            ps = round(price, 6) if price < 1 else round(price, 3)
            ss = round(sup, 6) if sup < 1 else round(sup, 3)
            t1 = round(price * 1.04, 6) if price < 1 else round(price * 1.04, 3)
            t2 = round(price * 1.08, 6) if price < 1 else round(price * 1.08, 3)
            slp = round(abs(price-sup)/price*100, 1)

            S(f"**#{count+1} BUY {sym}** RSI {int(rsi)} WR {int(wr)}%({tot}) Vol {round(vola*100,1)}%")
            S(f"Entry {ps} SL {ss}(-{slp}%) TP1 {t1}(+4%) TP2 {t2}(+8%)")
            S(f"💵 Cap ${invest} | Lev **{lev}X {lev_reason}** | Real TP1 +{4*lev}% TP2 +{8*lev}% SL -{round(slp*lev,1)}% | Bal ${round(bal,2)}")

            count = count + 1

    # ===== 5. 1X-5X MOON LIST =====
    if moon:
        moon_sorted = sorted(moon, key=lambda x: x[4], reverse=True)[:3]
        S("--------------------")
        S("🚀 **1X-5X POTENTIAL:**")
        for sym, rsi, price, lowd, pot, wr, tot in moon_sorted:
            ps = round(price, 6) if price < 1 else round(price, 3)
            S(f"🌙 {sym} RSI {int(rsi)} Price {ps} Pot **{round(pot,1)}X** WR {int(wr)}%({tot}) Low {round(lowd,6)}")

    data["balance"] = bal
    data["positions"] = pos
    SAVE(data)

    S(f"✅ **DONE** Bal ${round(bal,2)} Profit ${round(total_profit,2)} Trades {data.get('trades',0)} W/L {data.get('wins',0)}/{data.get('loss',0)} | $300 = 3x$100")

except Exception as e:
    S(f"❌ ERROR {str(e)[:200]}")
