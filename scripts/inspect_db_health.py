"""
Database reality check script for Phase 47.
"""
import sqlite3
import os
import json

db_path = "tradesignal.db"

def inspect():
    if not os.path.exists(db_path):
        print("Database tradesignal.db does not exist!")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print("Found tables:", tables)

    core_assets = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "BTCUSD", "ETHUSD", "XAUUSD", "NAS100", "SPX500"]
    asset_health = {}

    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cur.fetchone()[0]
        print(f"Table '{t}': {cnt} rows")

    if "historical_candles" in tables:
        print("\n--- 9 Core Assets in historical_candles ---")
        for asset in core_assets:
            cur.execute("""
                SELECT COUNT(*), MIN(timestamp), MAX(timestamp), timeframe
                FROM historical_candles
                WHERE symbol = ?
            """, (asset,))
            row = cur.fetchone()
            asset_health[asset] = {
                "count": row[0],
                "min_timestamp": row[1],
                "max_timestamp": row[2],
                "timeframe": row[3],
            }
            print(f"Asset {asset}: count={row[0]}, min={row[1]}, max={row[2]}, tf={row[3]}")

    if "signal_lifecycle" in tables:
        cur.execute("SELECT COUNT(*), status FROM signal_lifecycle GROUP BY status")
        print("\n--- signal_lifecycle Status breakdown ---")
        for r in cur.fetchall():
            print(f"Status '{r[1]}': {r[0]} rows")

    conn.close()

if __name__ == "__main__":
    inspect()
