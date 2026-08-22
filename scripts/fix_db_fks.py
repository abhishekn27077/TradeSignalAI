import sqlite3
import os

DB_PATH = r"d:\trading Bots\FinalTrade\TradeSignalAI-v3\trading_fallback.db"

def fix_foreign_keys():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("PRAGMA foreign_key_check;")
    errors = cur.fetchall()
    
    if not errors:
        print("No foreign key errors found.")
        return

    print(f"Found {len(errors)} foreign key errors. Attempting to fix...")
    
    # errors contains (table, rowid, parent, fkid)
    # To fix, we can delete the orphaned rows.
    # We group by table to do it efficiently.
    tables_to_fix = {}
    for err in errors:
        table = err['table']
        rowid = err['rowid']
        if table not in tables_to_fix:
            tables_to_fix[table] = []
        tables_to_fix[table].append(rowid)
        
    for table, rowids in tables_to_fix.items():
        print(f"Deleting {len(rowids)} orphaned rows from {table}...")
        # Delete in chunks to avoid massive queries
        chunk_size = 900
        for i in range(0, len(rowids), chunk_size):
            chunk = rowids[i:i+chunk_size]
            placeholders = ",".join(["?"] * len(chunk))
            cur.execute(f"DELETE FROM {table} WHERE rowid IN ({placeholders})", chunk)
            
    conn.commit()
    print("Fixed.")
    
    # Verify
    cur.execute("PRAGMA foreign_key_check;")
    new_errors = cur.fetchall()
    if new_errors:
        print(f"WARNING: Still {len(new_errors)} errors remaining.")
    else:
        print("Success: All foreign key errors resolved.")

if __name__ == "__main__":
    fix_foreign_keys()
