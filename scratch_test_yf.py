import asyncio
from app.market_data.providers.yfinance_provider import YFinanceDataProvider

async def main():
    provider = YFinanceDataProvider()
    rates = await provider.get_rates("BTCUSD", "1h", count=5)
    print(rates)

if __name__ == "__main__":
    asyncio.run(main())
