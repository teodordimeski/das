#!/usr/bin/env python3
"""
Filter3: Fill missing daily data

- Executed after Filter2 finishes on app startup, and once per day right after Filter2
- Filter3 starts only when Filter2 has completed successfully
- Connect to cryptoCoins database
- For each symbol, read last_available_date from cryptoSymbols table
- If this date is not yesterday (today-1), fetch the missing daily data and insert it
"""

import os
import sys
import time
import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# Database configuration - can be overridden by environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = "cryptoCoins"
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")

# Binance API configuration
BASE_URL = "https://api.binance.com"
MAX_WORKERS = 10
MAX_RETRIES = 5
RETRY_DELAY = 2
BATCH_SIZE = 1000


def safe_get(session, url, params=None, timeout=20):
    """Safe HTTP GET with retry logic"""
    backoff = RETRY_DELAY
    for attempt in range(1, MAX_RETRIES + 1):
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
            if attempt < MAX_RETRIES:
                time.sleep(backoff)
                backoff *= 1.7
            else:
                return None
    return None


def fetch_ohlcv_range(session, symbol, start_date, end_date):
    """Fetch OHLCV data for a symbol in a date range"""
    all_rows = []
    timeframe_ms = 86400000
    start_ts = int(datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc).timestamp() * 1000)
    end_ts = int(datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc).timestamp() * 1000)

    while start_ts <= end_ts:
        params = {
            "symbol": symbol,
            "interval": "1d",
            "startTime": start_ts,
            "endTime": min(start_ts + BATCH_SIZE * timeframe_ms - 1, end_ts),
            "limit": BATCH_SIZE
        }
        r = safe_get(session, f"{BASE_URL}/api/v3/klines", params=params)
        if not r:
            break
        batch = r.json()
        if not batch:
            break
        for row in batch:
            dt = datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc).date()
            all_rows.append({
                "date": dt,
                "open": float(row[1]) if row[1] else 0.0,
                "high": float(row[2]) if row[2] else 0.0,
                "low": float(row[3]) if row[3] else 0.0,
                "close": float(row[4]) if row[4] else 0.0,
                "volume": float(row[5]) if row[5] else 0.0,
                "quoteAssetVolume": float(row[7]) if row[7] else 0.0,
                "symbol": symbol
            })
        if len(batch) < BATCH_SIZE:
            break
        start_ts = batch[-1][0] + timeframe_ms
        time.sleep(0.2)

    return all_rows


def fetch_ticker(session, symbol):
    """Fetch 24hr ticker data for a symbol"""
    r = safe_get(session, f"{BASE_URL}/api/v3/ticker/24hr", params={"symbol": symbol})
    if not r:
        return {}
    t = r.json()
    return {
        "lastPrice_24h": float(t.get("lastPrice", 0)) if t.get("lastPrice") else 0.0,
        "volume_24h": float(t.get("volume", 0)) if t.get("volume") else 0.0,
        "quoteVolume_24h": float(t.get("quoteVolume", 0)) if t.get("quoteVolume") else 0.0,
        "high_24h": float(t.get("highPrice", 0)) if t.get("highPrice") else 0.0,
        "low_24h": float(t.get("lowPrice", 0)) if t.get("lowPrice") else 0.0
    }


def process_symbol(symbol, start_date, end_date):
    """Process a single symbol and return data rows"""
    session = requests.Session()
    try:
        ohlcv_data = fetch_ohlcv_range(session, symbol, start_date, end_date)
        if not ohlcv_data:
            return []
        
        ticker = fetch_ticker(session, symbol)
        
        # Enrich OHLCV data with ticker info
        for row in ohlcv_data:
            row.update({
                "lastPrice_24h": ticker.get("lastPrice_24h", 0.0),
                "volume_24h": ticker.get("volume_24h", 0.0),
                "quoteVolume_24h": ticker.get("quoteVolume_24h", 0.0),
                "high_24h": ticker.get("high_24h", 0.0),
                "low_24h": ticker.get("low_24h", 0.0),
                "baseAsset": symbol[:-4] if len(symbol) > 4 else symbol,
                "quoteAsset": symbol[-4:] if len(symbol) > 4 else "",
                "symbolUsed": symbol
            })
        
        return ohlcv_data
    finally:
        session.close()


def get_symbols_with_missing_data(conn, yesterday):
    """Get symbols that need data updates (last_available_date < yesterday) from latestInfo"""
    cursor = conn.cursor()
    try:
        # Read last_available_date from latestInfo table for each symbol
        # Only get symbols where last_available_date < yesterday (not equal)
        cursor.execute("""
            SELECT symbol, last_available_date
            FROM latestInfo
            WHERE last_available_date < %s
        """, (yesterday,))
        
        results = cursor.fetchall()
        return [(row[0], row[1]) for row in results]
    finally:
        cursor.close()


def get_all_symbols_status(conn, yesterday):
    """Get all symbols and their status for logging"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT symbol, last_available_date
            FROM latestInfo
            ORDER BY symbol
        """)
        return cursor.fetchall()
    finally:
        cursor.close()


def insert_symbol_data(conn, data_rows):
    """Insert symbol data into cryptoSymbols table"""
    if not data_rows:
        return 0
    
    cursor = conn.cursor()
    try:
        insert_query = """
            INSERT INTO cryptosymbols (
                date, open, high, low, close, volume, "quoteAssetVolume",
                symbol, "lastPrice_24h", "volume_24h", "quoteVolume_24h",
                "high_24h", "low_24h", "baseAsset", "quoteAsset", "symbolUsed"
            ) VALUES %s
            ON CONFLICT (symbol, date) DO NOTHING
        """
        
        values = [
            (
                row["date"],
                row["open"],
                row["high"],
                row["low"],
                row["close"],
                row["volume"],
                row["quoteAssetVolume"],
                row["symbol"],
                row["lastPrice_24h"],
                row["volume_24h"],
                row["quoteVolume_24h"],
                row["high_24h"],
                row["low_24h"],
                row.get("baseAsset") or "",
                row.get("quoteAsset") or "",
                row["symbolUsed"]
            )
            for row in data_rows
        ]
        
        execute_values(cursor, insert_query, values)
        conn.commit()
        return len(values)
    except Exception as e:
        conn.rollback()
        print(f"❌ Error inserting data for symbol: {e}")
        return 0
    finally:
        cursor.close()


def update_latest_date(conn, symbol, new_date):
    """Update latestInfo table with new latest date for a symbol"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO latestInfo (symbol, last_available_date)
            VALUES (%s, %s)
            ON CONFLICT (symbol) 
            DO UPDATE SET last_available_date = EXCLUDED.last_available_date
        """, (symbol, new_date))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"❌ Error updating latest date for {symbol}: {e}")
    finally:
        cursor.close()


def main():
    print("🚀 Starting Filter3: Filling missing daily data")
    
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    
    # Connect to cryptoCoins database
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        sys.exit(1)
    
    try:
        # Get all symbols status for logging
        all_symbols = get_all_symbols_status(conn, yesterday)
        symbols_to_update = get_symbols_with_missing_data(conn, yesterday)
        
        # Find symbols that are up to date (last_available_date == yesterday, which is today-1)
        up_to_date_symbols = [(s, d) for s, d in all_symbols if d == yesterday]
        if up_to_date_symbols:
            print(f"✅ {len(up_to_date_symbols)} symbol(s) already up to date (last_available_date == {yesterday}):")
            for symbol, last_date in up_to_date_symbols:
                print(f"   - {symbol}: {last_date} (no action needed)")
        
        if not symbols_to_update:
            if not up_to_date_symbols:
                print("✅ All symbols are up to date. No missing data to fetch.")
            return
        
        print(f"\n📊 Found {len(symbols_to_update)} symbol(s) with missing data:")
        for symbol, last_date in symbols_to_update:
            print(f"   - {symbol}: last_available_date = {last_date} (needs data up to {yesterday})")
        
        total_inserted = 0
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            
            for symbol, last_date in symbols_to_update:
                # Fetch data from day after last_date to yesterday
                start_date = last_date + timedelta(days=1)
                end_date = yesterday
                
                if start_date <= end_date:
                    futures[executor.submit(process_symbol, symbol, start_date, end_date)] = (symbol, last_date)
            
            completed = 0
            for future in as_completed(futures):
                symbol, last_date = futures[future]
                try:
                    data_rows = future.result()
                    if data_rows:
                        inserted = insert_symbol_data(conn, data_rows)
                        total_inserted += inserted
                        
                        # Update latest date if we inserted new data
                        if inserted > 0:
                            max_date = max(row["date"] for row in data_rows)
                            update_latest_date(conn, symbol, max_date)
                            missing_dates = f"{last_date + timedelta(days=1)} to {max_date}"
                            print(f"✅ {symbol}: Added {inserted} row(s) for dates {missing_dates} (was missing from {last_date})")
                        else:
                            print(f"⚠️  {symbol}: No new data inserted (may have been duplicates)")
                    else:
                        print(f"⚠️  {symbol}: No data fetched from API (last_date: {last_date})")
                    
                    completed += 1
                except Exception as e:
                    print(f"❌ Error processing {symbol}: {e}")
        
        print(f"✅ Filter3 completed! Inserted {total_inserted} new rows")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()

