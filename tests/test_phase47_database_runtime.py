"""
Phase 47 — Test Suite for Real Database Runtime Health.

Verifies:
  - SQLite database exists and is connectable
  - 9 core assets present with > 10,000 candles each
  - Zero null or invalid OHLC rows
"""
import os
import sqlite3
import pytest

CORE_ASSETS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "BTCUSD", "ETHUSD", "XAUUSD", "NAS100", "SPX500"]


class TestDatabaseRuntime:
    def test_database_file_exists(self):
        assert os.path.exists("tradesignal.db"), "tradesignal.db must exist in root directory"

    def test_core_assets_coverage(self):
        conn = sqlite3.connect("tradesignal.db")
        cur = conn.cursor()
        for asset in CORE_ASSETS:
            cur.execute("SELECT COUNT(*) FROM historical_candles WHERE symbol = ?", (asset,))
            count = cur.fetchone()[0]
            assert count > 10000, f"Asset {asset} has insufficient candle count ({count})"
        conn.close()

    def test_zero_null_or_invalid_candles(self):
        conn = sqlite3.connect("tradesignal.db")
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM historical_candles WHERE open IS NULL OR high IS NULL OR low IS NULL OR close IS NULL")
        null_cnt = cur.fetchone()[0]
        assert null_cnt == 0, f"Found {null_cnt} candles with NULL OHLC values"

        cur.execute("SELECT COUNT(*) FROM historical_candles WHERE high < low OR open < 0 OR close < 0")
        invalid_cnt = cur.fetchone()[0]
        assert invalid_cnt == 0, f"Found {invalid_cnt} invalid candles"
        conn.close()
