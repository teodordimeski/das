#!/usr/bin/env python3
"""
Stable Binance-only downloader (Version B2, 10 workers, timed, top 1000 by quoteVolume)
"""

import requests, time, os
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://api.binance.com"
CSV_FILE = "binance_data_top1000.csv"

MAX_WORKERS = 10
MAX_RETRIES = 5
RETRY_DELAY = 3

# =====================================================================================
# SAFE GET
# =====================================================================================
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

# =====================================================================================
# EXCHANGE INFO & TICKERS
# =====================================================================================
def get_exchange_info(session):
    r = safe_get(session, f"{BASE_URL}/api/v3/exchangeInfo")
    if not r:
        raise RuntimeError("Failed exchangeInfo")
    return r.json()["symbols"]

def get_all_tickers(session):
    r = safe_get(session, f"{BASE_URL}/api/v3/ticker/24hr")
    if not r:
        raise RuntimeError("Failed tickers")
    return r.json()

# =====================================================================================
# FETCH OHLCV DAILY HISTORY
# =====================================================================================
def fetch_ohlcv(session, symbol):
    limit = 1000
    all_rows = []
    since = int((datetime.utcnow() - timedelta(days=365*10)).timestamp() * 1000)
    timeframe_ms = 86400000

    while True:
        params = {"symbol": symbol, "interval": "1d", "limit": limit, "startTime": since}
        r = safe_get(session, f"{BASE_URL}/api/v3/klines", params=params)
        if not r: break
        batch = r.json()
        if not batch: break
        all_rows.extend(batch)
        last_ts = batch[-1][0]
        if len(batch) < limit: break
        since = last_ts + timeframe_ms
        time.sleep(0.2)

    if not all_rows: return None

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

# =====================================================================================
# FETCH TICKER 24H
# =====================================================================================
def fetch_ticker(session, symbol):
    r = safe_get(session, f"{BASE_URL}/api/v3/ticker/24hr", params={"symbol":symbol})
    return r.json() if r else {}

# =====================================================================================
# PROCESS ONE SYMBOL (TRADING PAIR)
# =====================================================================================
def process_symbol(s):
    session = requests.Session()
    try:
        if s["status"] != "TRADING":
            return None
        symbol = s["symbol"]
        df = fetch_ohlcv(session, symbol)
        if df is None:
            return None
        ticker = fetch_ticker(session, symbol)
        df["LastPrice_24h"] = float(ticker.get("lastPrice") or 0)
        df["Volume_24h"] = float(ticker.get("volume") or 0)
        df["QuoteVolume_24h"] = float(ticker.get("quoteVolume") or 0)
        df["High_24h"] = float(ticker.get("highPrice") or 0)
        df["Low_24h"] = float(ticker.get("lowPrice") or 0)
        df["BaseAsset"] = s["baseAsset"]
        df["QuoteAsset"] = s["quoteAsset"]
        df["SymbolUsed"] = symbol
        return df
    finally:
        session.close()

# =====================================================================================
# MAIN
# =====================================================================================
def main():
    start_time = time.time()
    session = requests.Session()
    try:
        symbols = get_exchange_info(session)
        tickers = get_all_tickers(session)
        print(f"🪙 Total symbols: {len(symbols)}")

        # Map symbol → quoteVolume
        ticker_map = {t["symbol"]: float(t.get("quoteVolume") or 0) for t in tickers}
        # Rank symbols by quoteVolume descending
        symbols_sorted = sorted([s for s in symbols if s["status"]=="TRADING"],
                                key=lambda s: ticker_map.get(s["symbol"],0), reverse=True)
        # Take top 1000
        top_symbols = symbols_sorted[:1000]
        print(f"📌 Top 1000 symbols selected based on quoteVolume")

        processed = set()
        if os.path.exists(CSV_FILE):
            try:
                old = pd.read_csv(CSV_FILE, usecols=["SymbolUsed"])
                processed = set(old["SymbolUsed"].unique())
            except: processed = set()

        to_process = [s for s in top_symbols if s["symbol"] not in processed]
        print(f"⏳ Remaining symbols to process: {len(to_process)}")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(process_symbol, s): s for s in to_process}
            completed_count = 0
            for fut in as_completed(futures):
                df = fut.result()
                completed_count += 1
                print(f"Progress: {completed_count}/{len(to_process)} symbols")
                if df is not None:
                    if os.path.exists(CSV_FILE):
                        df.to_csv(CSV_FILE, mode="a", header=False, index=False)
                    else:
                        df.to_csv(CSV_FILE, index=False)
                time.sleep(0.2)

    finally:
        session.close()
        elapsed = time.time() - start_time
        print(f"🎉 Finished: {CSV_FILE}")
        print(f"⏱️ Времетраење на процесот: {elapsed:.2f} секунди ({elapsed/60:.2f} минути)")

if __name__ == "__main__":
    main()
