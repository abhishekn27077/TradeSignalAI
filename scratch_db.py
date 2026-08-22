import sqlite3
conn = sqlite3.connect('trading_fallback.db')
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT timeframe FROM forecast_requests")
print("Timeframes:", cursor.fetchall())
