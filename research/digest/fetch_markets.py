#!/usr/bin/env python3
"""Collect market data for the morning digest.

Writes one JSON with 30-day daily series for key markets (Yahoo Finance)
and 30-day currency moves vs USD (ECB reference rates via Frankfurter).
Usage: python3 -I fetch_markets.py OUT.json
"""
import json, subprocess, sys, datetime as dt

def get(url):
    out = subprocess.run(["curl", "-sS", "-m", "25", "-L", "-A", "Mozilla/5.0", url],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip()[:200])
    return json.loads(out.stdout)

MARKETS = [  # id, Yahoo symbol, label, unit, decimals
    ("usdthb", "THB=X", "USD/THB", "฿", 2),
    ("eurthb", "EURTHB=X", "EUR/THB", "฿", 2),
    ("brent", "BZ=F", "Brent", "$", 2),
    ("gold", "GC=F", "Золото", "$", 0),
    ("spx", "^GSPC", "S&P 500", "", 0),
    ("btc", "BTC-USD", "Bitcoin", "$", 0),
    ("usdrub", "RUB=X", "USD/RUB", "₽", 2),
    ("ust10", "^TNX", "US 10Y", "%", 2),
]

def yahoo(sym):
    d = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1mo&interval=1d")
    r = d["chart"]["result"][0]
    ts = r["timestamp"]; cl = r["indicators"]["quote"][0]["close"]
    pts = [[dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d"), round(c, 4)]
           for t, c in zip(ts, cl) if c is not None]
    return pts

result = {"generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"), "markets": [], "fx": [], "errors": []}
for mid, sym, label, unit, dec in MARKETS:
    try:
        s = yahoo(sym)
        last, prev, first = s[-1][1], s[-2][1], s[0][1]
        result["markets"].append({
            "id": mid, "label": label, "unit": unit, "decimals": dec,
            "value": last, "date": s[-1][0],
            "change_1d_pct": round((last / prev - 1) * 100, 2),
            "change_30d_pct": round((last / first - 1) * 100, 2),
            "series": s,
            "source": {"name": "Yahoo Finance", "url": f"https://finance.yahoo.com/quote/{sym}"},
        })
    except Exception as e:  # report, never stop
        result["errors"].append(f"{label}: {e}")

ASIA = [("n225", "^N225", "Nikkei 225", "Япония"), ("kospi", "^KS11", "KOSPI", "Корея"),
        ("hsi", "^HSI", "Hang Seng", "Гонконг"), ("ssec", "000001.SS", "Shanghai", "Китай"),
        ("twii", "^TWII", "TAIEX", "Тайвань"), ("set", "^SET.BK", "SET", "Таиланд")]
result["asia"] = []
for mid, sym, label, country in ASIA:
    try:
        s = yahoo(sym)
        result["asia"].append({"id": mid, "label": label, "country": country, "value": s[-1][1], "date": s[-1][0],
                               "change_1d_pct": round((s[-1][1] / s[-2][1] - 1) * 100, 2),
                               "change_30d_pct": round((s[-1][1] / s[0][1] - 1) * 100, 2)})
    except Exception as e:
        result["errors"].append(f"{label}: {e}")

# Official Bank of Russia rate (primary source) to cross-check USD/RUB
try:
    import re
    xml = subprocess.run(["curl", "-sS", "-m", "25", "https://www.cbr.ru/scripts/XML_daily.asp"],
                         capture_output=True).stdout.decode("cp1251", "replace")
    date = re.search(r'Date="([^"]+)"', xml).group(1)
    usd = re.search(r"<CharCode>USD</CharCode>.*?<Value>([^<]+)</Value>", xml, re.S).group(1)
    result["cbr_usd"] = {"value": float(usd.replace(",", ".")), "date": date,
                         "source": {"name": "Банк России", "url": "https://www.cbr.ru/currency_base/daily/"}}
except Exception as e:
    result["errors"].append(f"CBR: {e}")

# Currencies vs USD over ~30 days, ECB reference rates (second, independent source)
try:
    start = (dt.date.today() - dt.timedelta(days=31)).isoformat()
    cur = "THB,CNY,JPY,KRW,IDR,MYR,INR,PHP,SGD,EUR"
    d = get(f"https://api.frankfurter.dev/v1/{start}..?base=USD&symbols={cur}")
    days = sorted(d["rates"])
    a, b = d["rates"][days[0]], d["rates"][days[-1]]
    names = {"THB": "Бат", "CNY": "Юань", "JPY": "Иена", "KRW": "Вона", "IDR": "Рупия", "MYR": "Ринггит",
             "INR": "Рупия (Индия)", "PHP": "Песо (Филиппины)", "SGD": "Сингап. доллар", "EUR": "Евро"}
    for c in cur.split(","):
        # positive = currency strengthened vs USD
        chg = round((a[c] / b[c] - 1) * 100, 2)
        result["fx"].append({"code": c, "name": names[c], "rate": b[c], "change_30d_pct": chg})
    result["fx_period"] = [days[0], days[-1]]
    result["fx_source"] = {"name": "ECB reference rates (Frankfurter)", "url": "https://www.frankfurter.app"}
except Exception as e:
    result["errors"].append(f"FX ECB: {e}")

json.dump(result, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
print("markets", len(result["markets"]), "fx", len(result["fx"]), "errors", result["errors"])
