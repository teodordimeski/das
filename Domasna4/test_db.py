#!/usr/bin/env python3
"""Quick database connection test"""
import psycopg2
import sys

try:
    print("Testing database connection...")
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='admin',
        database='cryptoCoins'
    )
    print("[OK] Connected to database!")
    
    cur = conn.cursor()
    
    # Check what tables exist
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    print(f"\nTables in database: {[t[0] for t in tables]}")
    
    # Find the actual table name (case-insensitive)
    table_name = None
    for t in tables:
        if 'cryptosymbol' in str(t[0]).lower():
            table_name = t[0]
            break
    
    if not table_name:
        print("[ERROR] Table 'cryptoSymbols' does not exist!")
        print("[INFO] The database needs to be initialized. Run Filter1.py to create tables.")
        conn.close()
        sys.exit(1)
    
    print(f"[INFO] Using table: {table_name}")
    
    # Use the actual table name (with quotes if it has mixed case)
    cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
    count = cur.fetchone()[0]
    print(f"[OK] Records in {table_name} table: {count}")
    
    # Check column names
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position;
    """)
    columns = cur.fetchall()
    print(f"\nColumns in {table_name}:")
    for col in columns:
        print(f"  {col[0]} ({col[1]})")
    
    if count > 0:
        cur.execute(f'SELECT symbol, date, close FROM "{table_name}" ORDER BY date DESC LIMIT 5')
        print("\nLast 5 records:")
        for row in cur.fetchall():
            print(f"  {row[0]} - {row[1]} - ${row[2]}")
    else:
        print("[WARNING] Database is empty! Python filters may not have run.")
    
    conn.close()
    sys.exit(0)
except psycopg2.OperationalError as e:
    print(f"[ERROR] Database connection error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error: {e}")
    sys.exit(1)

