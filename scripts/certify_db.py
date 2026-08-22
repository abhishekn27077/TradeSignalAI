import sqlite3
import os
import json

DB_PATH = r"d:\trading Bots\FinalTrade\TradeSignalAI-v3\trading_fallback.db"
ARTIFACT_DIR = r"C:\Users\Abhis\.gemini\antigravity-ide\brain\d1f3a00e-4c5b-494d-8d0b-14018e87107f"
REPORT_FILE = os.path.join(ARTIFACT_DIR, "database_certification.md")

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    report = ["# Database Certification Report\n"]
    
    # Check tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cur.fetchall()]
    report.append(f"## Tables Discovered ({len(tables)})\n")
    report.append(", ".join(tables) + "\n\n")

    # Check foreign keys and indexes
    cur.execute("PRAGMA foreign_key_check;")
    fk_errors = cur.fetchall()
    
    report.append("## Foreign Key Constraints\n")
    if not fk_errors:
        report.append("✅ PASS: No orphaned records or broken foreign key constraints found.\n\n")
    else:
        report.append(f"❌ FAIL: {len(fk_errors)} foreign key errors found.\n\n")
        
    cur.execute("PRAGMA integrity_check;")
    integrity = cur.fetchone()[0]
    report.append("## Integrity Check\n")
    if integrity == "ok":
        report.append("✅ PASS: Database integrity is 'ok'. No corruption found.\n\n")
    else:
        report.append(f"❌ FAIL: Integrity check failed: {integrity}\n\n")

    # Table specifics (Indexes, Rows)
    report.append("## Table Diagnostics\n")
    report.append("| Table Name | Row Count | Index Count | Null Corruption Check |\n")
    report.append("|---|---|---|---|\n")

    for table in tables:
        # row count
        cur.execute(f"SELECT COUNT(*) as c FROM {table};")
        row_count = cur.fetchone()['c']
        
        # index count
        cur.execute(f"PRAGMA index_list({table});")
        idx_count = len(cur.fetchall())
        
        # null checks for non-nullable cols
        cur.execute(f"PRAGMA table_info({table});")
        cols = cur.fetchall()
        null_issues = 0
        for col in cols:
            if col['notnull'] == 1:
                cur.execute(f"SELECT COUNT(*) as c FROM {table} WHERE {col['name']} IS NULL;")
                if cur.fetchone()['c'] > 0:
                    null_issues += 1
                    
        null_status = "✅ Clean" if null_issues == 0 else f"❌ {null_issues} Issues"
        
        report.append(f"| {table} | {row_count} | {idx_count} | {null_status} |\n")

    # Write report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
        
    print(f"Database certification complete. Wrote to {REPORT_FILE}")

if __name__ == "__main__":
    check_db()
