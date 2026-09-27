"""
scripts/migrate_market_data_schema.py
======================================
Phase 7 & Phase 25: Database Schema Migration for Timeframe & Venue Isolation.

Adds 'venue' column to historical_candles if missing, backfills venue for existing data,
and creates composite indexes for:
  (symbol, venue, timeframe, timestamp)
  (symbol, timeframe, timestamp)

Guarantees 100% backward compatibility with existing data while enforcing timeframe/venue isolation.
"""

import sqlite3
import os
import sys

DB_PATHS = ["tradesignal.db", "trading_fallback.db"]

def run_migration():
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            continue

        print(f"Migrating database: {db_path}...")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Check historical_candles table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historical_candles'")
        if not cur.fetchone():
            print(f"  historical_candles table not found in {db_path}, skipping.")
            conn.close()
            continue

        cur.execute("PRAGMA table_info(historical_candles)")
        cols = [c[1] for c in cur.fetchall()]

        if "venue" not in cols:
            print("  Adding 'venue' column...")
            cur.execute("ALTER TABLE historical_candles ADD COLUMN venue VARCHAR")

            cur.execute("""
                UPDATE historical_candles 
                SET venue = CASE 
                    WHEN symbol LIKE '%BTC%' OR symbol LIKE '%ETH%' THEN 'BINANCE'
                    WHEN symbol LIKE '%XAU%' THEN 'COMEX'
                    WHEN symbol LIKE '%NAS%' OR symbol LIKE '%SPX%' OR symbol LIKE '%US30%' THEN 'CME'
                    ELSE 'MT5_BROKER'
                END
                WHERE venue IS NULL OR venue = ''
            """)
            print("  Backfilled 'venue' column.")
        else:
            print("  'venue' column already present.")

        # Ensure composite indexes exist
        print("  Creating composite isolation indexes...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hc_sym_ven_tf_ts ON historical_candles(symbol, venue, timeframe, timestamp)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hc_sym_tf_ts ON historical_candles(symbol, timeframe, timestamp)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hc_tf_ts ON historical_candles(timeframe, timestamp)")

        conn.commit()
        conn.close()
        print(f"Successfully migrated {db_path}.")

if __name__ == "__main__":
    run_migration()
