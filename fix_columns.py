import sqlite3
import os

db_path = 'trading_fallback.db'
if not os.path.exists(db_path):
    print(f"DB not found: {db_path}")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

columns = [
    ("trace_id", "VARCHAR(36)"),
    ("duplicate_protection_hash", "VARCHAR(64)"),
    ("candle_timestamp", "DATETIME"),
    ("prediction_timestamp", "DATETIME"),
    ("data_age_seconds", "FLOAT"),
    ("data_freshness_status", "VARCHAR(20)"),
    ("model_trace", "JSON"),
    ("intelligence_snapshot", "JSON"),
    ("outcome", "VARCHAR(20)"),
    ("exit_price", "FLOAT"),
    ("exit_time", "DATETIME"),
    ("gross_pnl", "FLOAT"),
    ("spread_cost", "FLOAT"),
    ("slippage_cost", "FLOAT"),
    ("fees_cost", "FLOAT"),
    ("net_pnl", "FLOAT"),
    ("r_multiple", "FLOAT"),
    ("pnl", "FLOAT")
]

for col_name, col_type in columns:
    try:
        cursor.execute(f"ALTER TABLE signal_lifecycle ADD COLUMN {col_name} {col_type};")
        print(f"Added column {col_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"Column {col_name} already exists.")
        else:
            print(f"Error adding {col_name}: {e}")

conn.commit()
conn.close()
print("Done.")
