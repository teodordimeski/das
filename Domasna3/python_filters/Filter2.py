#!/usr/bin/env python3
"""
Filter2: Track latest available dates per symbol

- Executed after Filter1 finishes on app startup, and once per day after midnight
- Connect to cryptoCoins database
- Ensure latestInfo table exists with columns: symbol and last_available_date (no nulls)
- Write/update one row per symbol with its latest available date
"""

import os
import sys
import psycopg2
from psycopg2 import sql

# Database configuration - can be overridden by environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = "cryptoCoins"
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")


def create_latest_info_table_if_not_exists(conn):
    """Create latestInfo table if it doesn't exist"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS latestInfo (
                symbol VARCHAR(255) PRIMARY KEY,
                last_available_date DATE NOT NULL
            )
        """)
        conn.commit()
        print("✅ Table latestInfo created or already exists")
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating latestInfo table: {e}")
        return False
    finally:
        cursor.close()


def update_latest_dates(conn):
    """Update latestInfo table with latest available date for each symbol"""
    cursor = conn.cursor()
    try:
        # First, get all symbols and their latest dates from cryptoSymbols
        cursor.execute("""
            SELECT symbol, MAX(date) as last_available_date
            FROM cryptosymbols
            GROUP BY symbol
        """)
        
        symbol_dates = cursor.fetchall()
        
        if not symbol_dates:
            print("⚠️  No symbols found in cryptoSymbols table")
            return 0
        
        # Insert/update each symbol's latest date
        updated_symbols = []
        for symbol, last_date in symbol_dates:
            cursor.execute("""
                INSERT INTO latestInfo (symbol, last_available_date)
                VALUES (%s, %s)
                ON CONFLICT (symbol) 
                DO UPDATE SET last_available_date = EXCLUDED.last_available_date
            """, (symbol, last_date))
            updated_symbols.append((symbol, last_date))
        
        conn.commit()
        
        # Print each updated symbol
        print(f"✅ Updated latest dates for {len(updated_symbols)} symbols:")
        for symbol, last_date in updated_symbols:
            print(f"   - {symbol}: {last_date}")
        
        return len(updated_symbols)
    except Exception as e:
        conn.rollback()
        print(f"❌ Error updating latest dates: {e}")
        return 0
    finally:
        cursor.close()


def main():
    print("🚀 Starting Filter2: Tracking latest available dates")
    
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
        # Ensure latestInfo table exists
        if not create_latest_info_table_if_not_exists(conn):
            print("❌ Failed to create latestInfo table")
            sys.exit(1)
        
        # Update latest dates for all symbols
        update_latest_dates(conn)
        
        print("✅ Filter2 completed!")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
