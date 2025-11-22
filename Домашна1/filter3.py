#!/usr/bin/env python3
"""
Fetch missing Binance crypto data and append to top1000 CSV

- Чита missing.csv со симболи без податоци
- Влече сите достапни дневни OHLCV и 24h метрики
- Додава само уникатни записи во binance_data_top1000.csv
"""

import pandas as pd
import os
import requests
import time
from datetime import datetime, timedelta


MISSING_CSV = "missing.csv"
TOP1000_CSV = "binance_data_filter1_output.csv"
BASE_URL = "https://api.binance.com"
MAX_RETRIES = 5
RETRY_DELAY = 2

def safe_get(session, url, params=None):
    backoff = RETRY_DELAY
    for attempt in range(MAX_RETRIES):
        try:
            r = session.get(url, params=params, timeout=20)
            if r.status_code == 429:
                print(f"⚠️ 429 Rate limit, sleeping {backoff}s")
                time.sleep(backoff)
                backoff *= 1.5
                continue
            r.raise_for_status()
            time.sleep(0.15)
            return r.json()
        except Exception as e:
            print(f"⚠️ Request error {attempt+1}: {e}")
            time.sleep(backoff)
            backoff *= 1.5
    print(f"❌ Failed after retries: {url}")
    return None

def fetch_ohlcv(symbol):
    """Fetch last 10 years daily OHLCV data for a symbol"""
    session = requests.Session()
    limit = 1000
    all_rows = []
    start_time_ms = int((datetime.utcnow() - timedelta(days=365*10)).timestamp() * 1000)
    timeframe_ms = 86400000  # 1 day

    while True:
        params = {
            "symbol": symbol,
            "interval": "1d",
            "limit": limit,
            "startTime": start_time_ms
        }
        data = safe_get(session, f"{BASE_URL}/api/v3/klines", params=params)
        if not data or len(data) == 0:
            break
        all_rows.extend(data)
        last_ts = data[-1][0]
        if len(data) < limit:
            break
        start_time_ms = last_ts + timeframe_ms
        time.sleep(0.2)

    session.close()

    if not all_rows:
        return None

    df = pd.DataFrame(all_rows, columns=[
        "openTime","Open","High","Low","Close","Volume",
        "closeTime","QuoteAssetVolume","Trades","takerBaseVol",
        "takerQuoteVol","ignore"
    ])
    df["date"] = pd.to_datetime(df["openTime"], unit="ms").dt.date
    df = df[["date","Open","High","Low","Close","Volume","QuoteAssetVolume"]]
    for c in ["Open","High","Low","Close","Volume","QuoteAssetVolume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["symbol"] = symbol
    return df

def main():
    if not os.path.exists(MISSING_CSV):
        print(f"❌ Не постои missing.csv")
        return

    missing_df = pd.read_csv(MISSING_CSV)
    symbols = missing_df["symbol"].unique()

    # Чита постоечки top1000 CSV, ако не постои, создава празен DataFrame
    if os.path.exists(TOP1000_CSV):
        top_df = pd.read_csv(TOP1000_CSV, parse_dates=["date"])
    else:
        top_df = pd.DataFrame(columns=["date","Open","High","Low","Close","Volume","QuoteAssetVolume","symbol"])

    session = requests.Session()
    for idx, sym in enumerate(symbols, start=1):
        print(f"⏳ {idx}/{len(symbols)} → Processing {sym}")
        df_new = fetch_ohlcv(sym)
        if df_new is not None and len(df_new) > 0:
            # Проверка за дупликати по symbol + date
            if not top_df.empty:
                merged = pd.merge(df_new, top_df, on=["symbol","date"], how="left", indicator=True)
                df_new = merged[merged["_merge"]=="left_only"]
                df_new = df_new[df_new.columns[:8]]  # задржи оригиналните колони
            # Додај во CSV
            if len(df_new) > 0:
                top_df = pd.concat([top_df, df_new], ignore_index=True)
                top_df.to_csv(TOP1000_CSV, index=False)
                print(f"✅ {sym} → Added {len(df_new)} new rows")
            else:
                print(f"⚠️ {sym} → All data already exists, skipped")
        else:
            print(f"⚠️ {sym} → No OHLCV data fetched")

    session.close()
    print(f"🎉 Finished updating {TOP1000_CSV}")

if __name__ == "__main__":
    main()
