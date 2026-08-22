import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.strategies.SmartMoney.PremiumDiscount.range_engine import (
    PremiumDiscountEngine, DealingRange, ZoneType
)


def test_premium_discount_engine():
    n = 30
    dates = [datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc) + timedelta(hours=i) for i in range(n)]

    # Dealing range: Low = 100, High = 200, Close = 120 (Discount)
    df = pd.DataFrame({
        'timestamp': dates,
        'open': [150.0] * n,
        'high': [155.0] * n,
        'low': [145.0] * n,
        'close': [150.0] * n,
    })
    df.loc[5, 'high'] = 200.0
    df.loc[10, 'low'] = 100.0
    df.loc[29, 'close'] = 120.0  # Discount zone (< 50% = 150)

    engine = PremiumDiscountEngine(swing_len=2)
    dr = engine.evaluate_range(df, asset="BTCUSD", timeframe="1H")

    assert dr.range_high >= 199.0
    assert dr.range_low <= 101.0
    assert dr.equilibrium_50 == (dr.range_high + dr.range_low) / 2.0
    assert dr.zone == ZoneType.DISCOUNT
    assert dr.premium_discount_pct < 0.50
