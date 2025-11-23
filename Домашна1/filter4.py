#!/usr/bin/env python3
"""
Stable Binance downloader: update binance_data_filter1_output.csv
based on last date in binance_data_filter2_output.csv
"""

import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://api.binance.com"
FILTER1_CSV = "binance_data_filter1_output.csv"
FILTER2_CSV = "binance_data_filter2_output.csv"
MAX_WORKERS = 10
MAX_RETRIES = 5
RETRY_DELAY = 2
BATCH_SIZE = 1000

COLUMNS = ["date","Open","High","Low","Close","Volume","QuoteAssetVolume",
           "symbol","LastPrice_24h","Volume_24h","QuoteVolume_24h",
           "High_24h","Low_24h","BaseAsset","QuoteAsset","SymbolUsed"]

def safe_get(session, url, params=None, timeout=20):
    backoff = RETRY_DELAY
    for attempt in range(1, MAX_RETRIES+1):
        try:
            r = session.get(url, params=params, timeout=timeout)
            if r.status_code == 429:
                time.sleep(backoff)
                backoff *= 1.7
                continue
            r.raise_for_status()
            time.sleep(0.15)
            return r
        except Exception:
            time.sleep(backoff)
            backoff *= 1.7
    return None

def fetch_ohlcv_range(session, symbol, start_date, end_date):
    all_rows = []
    timeframe_ms = 86400000
    start_ts = int(datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc).timestamp() * 1000)
    end_ts = int(datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc).timestamp() * 1000)

    while start_ts <= end_ts:
        params = {
            "symbol": symbol,
            "interval": "1d",
            "startTime": start_ts,
            "endTime": min(start_ts + BATCH_SIZE*timeframe_ms - 1, end_ts),
            "limit": BATCH_SIZE
        }
        r = safe_get(session, f"{BASE_URL}/api/v3/klines", params=params)
        if not r: break
        batch = r.json()
        if not batch: break
        for row in batch:
            dt = datetime.fromtimestamp(row[0]/1000, tz=timezone.utc).date()
            all_rows.append({
                "date": pd.Timestamp(dt),
                "Open": float(row[1]),
                "High": float(row[2]),
                "Low": float(row[3]),
                "Close": float(row[4]),
                "Volume": float(row[5]),
                "QuoteAssetVolume": float(row[7]),
                "symbol": symbol,
                "LastPrice_24h": None,
                "Volume_24h": None,
                "QuoteVolume_24h": None,
                "High_24h": None,
                "Low_24h": None,
                "BaseAsset": None,
                "QuoteAsset": None,
                "SymbolUsed": symbol
            })
        if len(batch) < BATCH_SIZE: break
        start_ts = batch[-1][0] + timeframe_ms
        time.sleep(0.2)

    if not all_rows: return None
    return pd.DataFrame(all_rows)

def fetch_ticker(session, symbol):
    r = safe_get(session, f"{BASE_URL}/api/v3/ticker/24hr", params={"symbol": symbol})
    if not r: return {}
    t = r.json()
    return {
        "LastPrice_24h": float(t.get("lastPrice",0)),
        "Volume_24h": float(t.get("volume",0)),
        "QuoteVolume_24h": float(t.get("quoteVolume",0)),
        "High_24h": float(t.get("highPrice",0)),
        "Low_24h": float(t.get("lowPrice",0))
    }

def process_symbol(symbol, start_date, end_date):
    session = requests.Session()
    try:
        df = fetch_ohlcv_range(session, symbol, start_date, end_date)
        if df is None or df.empty: return None
        ticker = fetch_ticker(session, symbol)
        for col in ["LastPrice_24h","Volume_24h","QuoteVolume_24h","High_24h","Low_24h"]:
            df[col] = ticker.get(col)
        df["BaseAsset"] = symbol[:-4]  # simplification
        df["QuoteAsset"] = symbol[-4:]  # simplification
        df["SymbolUsed"] = symbol
        return df[COLUMNS]
    finally:
        session.close()

def main():
    os.chdir('/Users/teodordimeski/Documents/Faks/semestar V/dizajn i arhitektura na softver/domasni/Domasna 1/SoTimer10Workers')

    if not os.path.exists(FILTER2_CSV):
        print(f"❌ Не постои {FILTER2_CSV}")
        return

    df_last = pd.read_csv(FILTER2_CSV, parse_dates=["date"])
    df_last["date"] = pd.to_datetime(df_last["date"])
    today = datetime.now(timezone.utc).date()

    if os.path.exists(FILTER1_CSV):
        df_existing = pd.read_csv(FILTER1_CSV, parse_dates=["date"])
        df_existing["date"] = pd.to_datetime(df_existing["date"])
    else:
        df_existing = pd.DataFrame(columns=COLUMNS)

    total_rows_added = 0
    symbols_updated = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for _, row in df_last.iterrows():
            sym = row["symbol"]
            last_date = row["date"].date()
            if last_date >= today:
                continue
            symbols_updated += 1
            start_date = last_date + timedelta(days=1)
            futures[executor.submit(process_symbol, sym, start_date, today)] = sym

        completed = 0
        for fut in as_completed(futures):
            sym = futures[fut]
            try:
                df_new = fut.result()
                completed += 1
                print(f"Progress: {completed}/{len(futures)} symbols ({sym})")
                if df_new is not None and not df_new.empty:
                    # concat + drop_duplicates instead of merge
                    df_existing = pd.concat([df_existing, df_new], ignore_index=True)
                    df_existing.drop_duplicates(subset=["symbol","date"], inplace=True)
                    total_rows_added += len(df_new)
            except Exception as e:
                print(f"❌ Error processing {sym}: {e}")

    df_existing.to_csv(FILTER1_CSV, index=False)
    print(f"🎉 Finished! Total symbols updated: {symbols_updated}, total rows added: {total_rows_added}")

if __name__ == "__main__":
    main()
