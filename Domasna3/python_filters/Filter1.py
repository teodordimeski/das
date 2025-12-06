#!/usr/bin/env python3
"""
Filter1: Database initialization and initial data population

- Connect to PostgreSQL as superuser/CREATEDB user
- Create cryptoCoins database if it doesn't exist
- Connect to cryptoCoins database
- Create cryptoSymbols table matching Java CryptoSymbol model
- Download data from Binance (top 1000 symbols by quoteVolume, 10 years history)
- Filter out invalid symbols (based on filter1 logic from mycode)
- If table exists and has data, do nothing
"""

import os
import sys
import time
import requests
import psycopg2
from psycopg2.extras import execute_values
from psycopg2 import sql
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# Database configuration - can be overridden by environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_SUPERUSER = os.getenv("DB_SUPERUSER", "postgres")
DB_SUPERUSER_PASSWORD = os.getenv("DB_SUPERUSER_PASSWORD", "admin")
DB_NAME = "cryptoCoins"
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")

# Binance API configuration
BASE_URL = "https://api.binance.com"
MIN_QUOTE_VOLUME = 10000
STABLE_QUOTES = {"USDT", "BUSD", "USDC", "USD", "BTC", "ETH"}

MAX_WORKERS = 10
MAX_RETRIES = 5
RETRY_DELAY = 3
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


def get_exchange_info(session):
    """Get exchange info with all symbols"""
    r = safe_get(session, f"{BASE_URL}/api/v3/exchangeInfo")
    if not r:
        raise RuntimeError("Failed to get exchangeInfo")
    return r.json()["symbols"]


def get_all_tickers(session):
    """Get all 24hr ticker statistics"""
    r = safe_get(session, f"{BASE_URL}/api/v3/ticker/24hr")
    if not r:
        raise RuntimeError("Failed to get tickers")
    return r.json()


def fetch_ohlcv(session, symbol):
    """Fetch OHLCV daily history for a symbol (10 years)"""
    limit = 1000
    all_rows = []
    since = int((datetime.now(timezone.utc) - timedelta(days=365*10)).timestamp() * 1000)
    timeframe_ms = 86400000

    while True:
        params = {"symbol": symbol, "interval": "1d", "limit": limit, "startTime": since}
        r = safe_get(session, f"{BASE_URL}/api/v3/klines", params=params)
        if not r:
            break
        batch = r.json()
        if not batch:
            break
        all_rows.extend(batch)
        last_ts = batch[-1][0]
        if len(batch) < limit:
            break
        since = last_ts + timeframe_ms
        time.sleep(0.2)

    if not all_rows:
        return None

    # Convert to our format
    result = []
    for row in all_rows:
        dt = datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc).date()
        result.append({
            "date": dt,
            "open": float(row[1]) if row[1] else 0.0,
            "high": float(row[2]) if row[2] else 0.0,
            "low": float(row[3]) if row[3] else 0.0,
            "close": float(row[4]) if row[4] else 0.0,
            "volume": float(row[5]) if row[5] else 0.0,
            "quoteAssetVolume": float(row[7]) if row[7] else 0.0,
            "symbol": symbol
        })
    return result


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


def process_symbol(symbol_info, ticker_map):
    """Process one symbol - download data and return rows"""
    session = requests.Session()
    try:
        if symbol_info["status"] != "TRADING":
            return None
        
        symbol = symbol_info["symbol"]
        base_asset = symbol_info["baseAsset"]
        quote_asset = symbol_info["quoteAsset"]
        
        # Fetch OHLCV data
        ohlcv_data = fetch_ohlcv(session, symbol)
        if not ohlcv_data:
            return None
        
        # Fetch ticker data
        ticker = fetch_ticker(session, symbol)
        
        # Apply filter1 logic: filter out invalid symbols
        # LastPrice_24h > 0, QuoteVolume_24h >= MIN_QUOTE_VOLUME, QuoteAsset in STABLE_QUOTES
        if (ticker.get("lastPrice_24h", 0) <= 0 or
            ticker.get("quoteVolume_24h", 0) < MIN_QUOTE_VOLUME or
            quote_asset not in STABLE_QUOTES):
            return None  # Symbol doesn't pass filter1 criteria
        
        # Symbol is valid, enrich all rows with ticker data
        valid_rows = []
        for row in ohlcv_data:
                # Enrich row with ticker data
                row.update({
                    "lastPrice_24h": ticker.get("lastPrice_24h", 0.0),
                    "volume_24h": ticker.get("volume_24h", 0.0),
                    "quoteVolume_24h": ticker.get("quoteVolume_24h", 0.0),
                    "high_24h": ticker.get("high_24h", 0.0),
                    "low_24h": ticker.get("low_24h", 0.0),
                    "baseAsset": base_asset,
                    "quoteAsset": quote_asset,
                    "symbolUsed": symbol
                })
                valid_rows.append(row)
        
        return valid_rows if valid_rows else None
    finally:
        session.close()


def create_database_if_not_exists():
    """Create database if it doesn't exist (requires superuser)"""
    try:
        # Connect to postgres database as superuser
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_SUPERUSER,
            password=DB_SUPERUSER_PASSWORD,
            database="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
            print(f"✅ Created database: {DB_NAME}")
        else:
            print(f"✅ Database {DB_NAME} already exists")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False


def create_table_if_not_exists(conn):
    """Create cryptoSymbols table if it doesn't exist"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cryptosymbols (
                id BIGSERIAL PRIMARY KEY,
                date DATE NOT NULL,
                open DOUBLE PRECISION NOT NULL DEFAULT 0,
                high DOUBLE PRECISION NOT NULL DEFAULT 0,
                low DOUBLE PRECISION NOT NULL DEFAULT 0,
                close DOUBLE PRECISION NOT NULL DEFAULT 0,
                volume DOUBLE PRECISION NOT NULL DEFAULT 0,
                "quoteAssetVolume" DOUBLE PRECISION NOT NULL DEFAULT 0,
                symbol VARCHAR(255) NOT NULL,
                "lastPrice_24h" DOUBLE PRECISION NOT NULL DEFAULT 0,
                "volume_24h" DOUBLE PRECISION NOT NULL DEFAULT 0,
                "quoteVolume_24h" DOUBLE PRECISION NOT NULL DEFAULT 0,
                "high_24h" DOUBLE PRECISION NOT NULL DEFAULT 0,
                "low_24h" DOUBLE PRECISION NOT NULL DEFAULT 0,
                "baseAsset" VARCHAR(255) NOT NULL DEFAULT '',
                "quoteAsset" VARCHAR(255) NOT NULL DEFAULT '',
                "symbolUsed" VARCHAR(255) NOT NULL,
                UNIQUE(symbol, date)
            )
        """)
        conn.commit()
        print("✅ Table cryptoSymbols created or already exists")
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating table: {e}")
        return False
    finally:
        cursor.close()


def table_has_data(conn):
    """Check if cryptoSymbols table has data"""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM cryptosymbols")
        count = cursor.fetchone()[0]
        print(f"📊 Table cryptoSymbols currently has {count} rows")
        return count > 0
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
        inserted_count = cursor.rowcount
        conn.commit()
        return inserted_count
    except Exception as e:
        conn.rollback()
        print(f"❌ Error inserting data: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        cursor.close()


def main():
    print("🚀 Starting Filter1: Database initialization and data population")
    
    # Step 1: Create database if it doesn't exist
    print(f"🔍 Checking if database '{DB_NAME}' exists...")
    if not create_database_if_not_exists():
        print("❌ Failed to create database")
        sys.exit(1)
    
    # Step 2: Connect to cryptoCoins database
    print(f"🔌 Connecting to database: {DB_NAME}")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        print(f"✅ Connected to database: {DB_NAME}")
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        sys.exit(1)
    
    try:
        # Step 3: Create table if it doesn't exist
        print("🔍 Checking if table 'cryptoSymbols' exists...")
        if not create_table_if_not_exists(conn):
            print("❌ Failed to create table")
            sys.exit(1)
        
        # Step 4: Check if table has data
        print("🔍 Checking if table 'cryptoSymbols' contains data...")
        if table_has_data(conn):
            print("✅ Table cryptoSymbols already contains data. Skipping data population.")
            return
        print("📝 Table is empty or newly created. Proceeding with data population...")
        
        # Step 5: Get exchange info and tickers (crypto_downloader logic)
        print("📥 Fetching exchange info and ticker data from Binance...")
        session = requests.Session()
        try:
            symbols = get_exchange_info(session)
            tickers = get_all_tickers(session)
            print(f"🪙 Total symbols: {len(symbols)}")
            
            # Map symbol → ticker data
            ticker_map = {}
            for t in tickers:
                ticker_map[t["symbol"]] = {
                    "quoteVolume": float(t.get("quoteVolume") or 0)
                }
            
            # Rank symbols by quoteVolume descending, take top 1000
            symbols_sorted = sorted(
                [s for s in symbols if s["status"] == "TRADING"],
                key=lambda s: ticker_map.get(s["symbol"], {}).get("quoteVolume", 0),
                reverse=True
            )
            top_symbols = symbols_sorted[:1000]
            print(f"📌 Top 1000 symbols selected based on quoteVolume")
            
        finally:
            session.close()
        
        # Step 6: Process symbols and insert valid data (with filter1 filtering)
        print(f"📊 Processing {len(top_symbols)} symbols and applying filter1 validation...")
        total_inserted = 0
        valid_symbols_count = 0
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(process_symbol, s, ticker_map): s 
                for s in top_symbols
            }
            
            completed = 0
            for future in as_completed(futures):
                symbol_info = futures[future]
                symbol = symbol_info["symbol"]
                try:
                    data_rows = future.result()
                    if data_rows:
                        inserted = insert_symbol_data(conn, data_rows)
                        total_inserted += inserted
                        valid_symbols_count += 1
                        if inserted == 0:
                            print(f"⚠️  {symbol}: Fetched {len(data_rows)} rows but 0 were inserted (may be duplicates)")
                        else:
                            print(f"✅ {symbol}: Inserted {inserted} rows")
                    else:
                        print(f"⚠️  {symbol}: No valid data (filtered out by filter1 criteria)")
                    completed += 1
                    if completed % 50 == 0:
                        print(f"Progress: {completed}/{len(top_symbols)} symbols - {total_inserted} rows inserted, {valid_symbols_count} valid symbols")
                except Exception as e:
                    print(f"❌ Error processing {symbol}: {e}")
                    import traceback
                    traceback.print_exc()
        
        print(f"✅ Filter1 completed! Inserted {total_inserted} rows from {valid_symbols_count} valid symbols into cryptoSymbols table")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
