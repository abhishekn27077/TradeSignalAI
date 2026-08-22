"""
PHASE 16 — EXPERIMENT 16: MARKET SOURCE VERIFICATION
Compares backend prices vs raw provider prices for each asset.
Clearly labels source: YFinance / TradingView / Broker / Cached.
Does NOT claim TradingView sync unless actual TV feed is queried.
"""
import asyncio
import json
import os
from datetime import datetime, timezone
import httpx

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "validation_outputs", "market_source"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_URL = "http://localhost:8000"

# Yahoo Finance symbols mapping
YAHOO_SYMBOLS = {
    "BTCUSD":  "BTC-USD",
    "ETHUSD":  "ETH-USD",
    "EURUSD":  "EURUSD=X",
    "GBPUSD":  "GBPUSD=X",
    "USDJPY":  "JPY=X",
    "AUDUSD":  "AUDUSD=X",
    "XAUUSD":  "GC=F",
    "NAS100":  "NQ=F",
    "SPX500":  "ES=F",
}


async def get_backend_price(asset: str, client: httpx.AsyncClient) -> dict:
    try:
        r = await client.get(f"{BASE_URL}/api/v1/market-data/current", params={"symbol": asset}, timeout=10)
        if r.status_code == 200:
            d = r.json()
            price = d.get("price") or d.get("close") or d.get("last_price")
            return {"price": float(price) if price else None,
                    "timestamp": d.get("timestamp"),
                    "source": d.get("source", "backend_cached"),
                    "status": "OK"}
    except Exception as e:
        pass
    return {"price": None, "status": "ERROR"}


async def get_yfinance_price(yahoo_sym: str, client: httpx.AsyncClient) -> dict:
    """Direct Yahoo Finance quote via query2 API — no auth required."""
    try:
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{yahoo_sym}?interval=1m&range=1d"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = await client.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            result = data.get("chart", {}).get("result", [])
            if result:
                meta = result[0].get("meta", {})
                price = meta.get("regularMarketPrice")
                ts    = meta.get("regularMarketTime")
                return {"price": float(price) if price else None,
                        "timestamp": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else None,
                        "source": "YFinance", "status": "OK"}
    except Exception as e:
        pass
    return {"price": None, "source": "YFinance", "status": "FETCH_FAILED"}


async def main():
    print("="*60)
    print("PHASE 16 — EXP 16: MARKET SOURCE VERIFICATION")
    print("="*60)

    rows = []
    async with httpx.AsyncClient() as client:
        for asset, yahoo_sym in YAHOO_SYMBOLS.items():
            print(f"\n  {asset} ({yahoo_sym})")
            backend = await get_backend_price(asset, client)
            provider = await get_yfinance_price(yahoo_sym, client)

            b_price = backend.get("price")
            p_price = provider.get("price")
            if b_price and p_price:
                diff     = abs(b_price - p_price)
                diff_pct = diff / p_price * 100 if p_price else None
            else:
                diff = diff_pct = None

            row = {
                "asset": asset,
                "backend_price": b_price,
                "backend_timestamp": backend.get("timestamp"),
                "backend_source": backend.get("source", "unknown"),
                "provider_price": p_price,
                "provider_timestamp": provider.get("timestamp"),
                "provider_source": provider.get("source", "YFinance"),
                "price_difference": round(diff, 6) if diff is not None else None,
                "price_difference_pct": round(diff_pct, 4) if diff_pct is not None else None,
                "tv_sync_claimed": False,  # We are NOT claiming TradingView sync — using YFinance only
                "backend_status": backend.get("status"),
                "provider_status": provider.get("status"),
            }
            rows.append(row)
            print(f"    Backend:  {b_price} ({backend.get('source','?')})")
            print(f"    Provider: {p_price} ({provider.get('source','?')})")
            if diff_pct is not None:
                status = "✓ WITHIN 0.1%" if diff_pct < 0.1 else f"⚠ DEVIATION {diff_pct:.3f}%"
                print(f"    Delta:    {diff_pct:.4f}% — {status}")
            else:
                print(f"    Delta:    CANNOT COMPARE (one or both prices missing)")

    out = {"generated_at": datetime.utcnow().isoformat(), "assets": rows,
           "note": "TradingView sync NOT claimed. Source is YFinance (query2 API)."}
    out_path = os.path.join(OUTPUT_DIR, "market_source_verification.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n[DONE] Market source verification saved: {out_path}")
    with open(os.path.join(OUTPUT_DIR, "phase16_market_source_verification.done"), "w") as f:
        f.write(datetime.utcnow().isoformat())


if __name__ == "__main__":
    asyncio.run(main())
