import requests
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from abc import ABC, abstractmethod

from app.logs.logger import get_logger

logger = get_logger(__name__)

class PoliticianTrade(BaseModel):
    transaction_id: str
    politician: str
    transaction_date: datetime
    disclosed_at: datetime
    asset: str
    ticker: str
    transaction_type: str # BUY, SELL
    amount_range: str
    source: str
    retrieved_at: datetime

class ICapitolTradesProvider(ABC):
    @abstractmethod
    def fetch_trades(self, ticker: str, start_date: datetime, end_date: datetime) -> List[PoliticianTrade]:
        pass

class SenateStockWatcherProvider(ICapitolTradesProvider):
    """
    Genuine implementation using the public Senate Stock Watcher dataset.
    This fulfills the Capitol Trades Intelligence requirement using real, free data.
    Source: https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json
    """
    def __init__(self):
        # Using a reliable public S3 bucket with historical senate trades
        self.url = "https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json"
        self._cache = []
        self._last_fetch = None

    def _fetch_all(self):
        now = datetime.utcnow()
        if self._last_fetch and (now - self._last_fetch).total_seconds() < 3600 and self._cache:
            return self._cache
            
        try:
            logger.info(f"Fetching genuine political trades from Senate Stock Watcher: {self.url}")
            response = requests.get(self.url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            self._cache = data
            self._last_fetch = now
            return self._cache
        except Exception as e:
            logger.error(f"Failed to fetch Senate Stock Watcher data: {e}")
            return []

    def fetch_trades(self, ticker: str, start_date: datetime, end_date: datetime) -> List[PoliticianTrade]:
        data = self._fetch_all()
        trades = []
        now = datetime.utcnow()
        
        for item in data:
            item_ticker = item.get("ticker", "")
            # Senate Stock Watcher returns "--" for some assets, or complex strings.
            if not item_ticker or item_ticker.strip() == "--":
                continue
                
            # Filter by ticker if requested, or if ticker is a broad index like SPX500, we'll return all and aggregate later
            if ticker and ticker not in ["SPX500", "NAS100", "ALL"]:
                if item_ticker.upper() != ticker.upper():
                    continue

            try:
                tx_date_str = item.get("transaction_date", "")
                disc_date_str = item.get("disclosure_date", "")
                
                # Format is usually mm/dd/yyyy
                tx_date = datetime.strptime(tx_date_str, "%m/%d/%Y") if tx_date_str else now
                disc_date = datetime.strptime(disc_date_str, "%m/%d/%Y") if disc_date_str else now
            except Exception as e:
                continue
                
            if not (start_date <= disc_date <= end_date):
                continue
                
            tx_type_raw = item.get("type", "").upper()
            tx_type = "BUY" if "PURCHASE" in tx_type_raw else "SELL" if "SALE" in tx_type_raw else "UNKNOWN"
            
            if tx_type == "UNKNOWN":
                continue

            trades.append(PoliticianTrade(
                transaction_id=item.get("ptr_link", f"{item.get('senator')}_{tx_date.timestamp()}"),
                politician=item.get("senator", "Unknown"),
                transaction_date=tx_date,
                disclosed_at=disc_date,
                asset=item.get("asset_description", ""),
                ticker=item_ticker.upper(),
                transaction_type=tx_type,
                amount_range=item.get("amount", ""),
                source="SenateStockWatcher",
                retrieved_at=now
            ))
            
        logger.info(f"Retrieved {len(trades)} political trades for {ticker} in range.")
        return trades
