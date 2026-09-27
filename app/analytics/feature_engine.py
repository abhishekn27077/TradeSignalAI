import pandas as pd
import numpy as np
import ta

class FeatureEngine:
    """
    Institutional Feature Engineering Pipeline.
    Calculates 50+ quantitative features from raw OHLCV data.
    """
    
    @staticmethod
    def add_all_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds all required features to the OHLCV dataframe.
        Expected columns: open, high, low, close, volume. Index should be datetime.
        """
        if df.empty or len(df) < 50:
            return df
            
        df = df.copy()
        
        # 1. Momentum Indicators
        df['RSI_14'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()
        macd = ta.trend.MACD(close=df['close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['MACD_diff'] = macd.macd_diff()
        
        stoch = ta.momentum.StochasticOscillator(high=df['high'], low=df['low'], close=df['close'])
        df['Stoch_K'] = stoch.stoch()
        df['Stoch_D'] = stoch.stoch_signal()
        
        df['CCI_20'] = ta.trend.CCIIndicator(high=df['high'], low=df['low'], close=df['close'], window=20).cci()
        df['Momentum_10'] = df['close'].diff(10)
        df['ROC_10'] = ta.momentum.ROCIndicator(close=df['close'], window=10).roc()

        # 2. Trend Indicators (EMAs, SMAs & ADX)
        df['EMA_20'] = ta.trend.EMAIndicator(close=df['close'], window=20).ema_indicator()
        df['EMA_50'] = ta.trend.EMAIndicator(close=df['close'], window=50).ema_indicator()
        if len(df) >= 200:
            df['EMA_200'] = ta.trend.EMAIndicator(close=df['close'], window=200).ema_indicator()
        else:
            df['EMA_200'] = ta.trend.EMAIndicator(close=df['close'], window=min(len(df), 50)).ema_indicator()
        
        df['SMA_20'] = ta.trend.SMAIndicator(close=df['close'], window=20).sma_indicator()
        df['SMA_50'] = ta.trend.SMAIndicator(close=df['close'], window=50).sma_indicator()
        
        adx = ta.trend.ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=14)
        df['ADX'] = adx.adx()
        df['DI_plus'] = adx.adx_pos()
        df['DI_minus'] = adx.adx_neg()

        # 3. Volatility Indicators
        df['ATR_14'] = ta.volatility.AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14).average_true_range()
        bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
        df['BB_high'] = bb.bollinger_hband()
        df['BB_low'] = bb.bollinger_lband()
        df['Volatility_20'] = df['close'].rolling(20).std()

        # 4. Volume Indicators
        if df['volume'].sum() == 0:
            df['OBV'] = 0
            df['VWAP'] = df['close']
            df['MFI_14'] = 50
            df['CMF_20'] = 0
            df['Liquidity_proxy'] = 0
        else:
            df['OBV'] = ta.volume.OnBalanceVolumeIndicator(close=df['close'], volume=df['volume']).on_balance_volume()
            df['VWAP'] = ta.volume.VolumeWeightedAveragePrice(high=df['high'], low=df['low'], close=df['close'], volume=df['volume']).volume_weighted_average_price()
            df['MFI_14'] = ta.volume.MFIIndicator(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'], window=14).money_flow_index()
            df['CMF_20'] = ta.volume.ChaikinMoneyFlowIndicator(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'], window=20).chaikin_money_flow()
            df['Liquidity_proxy'] = df['close'] * df['volume']
            
        # Fill any remaining NaNs in volume indicators if volume was partially 0
        for col in ['VWAP', 'MFI_14', 'CMF_20', 'OBV', 'Liquidity_proxy']:
            df[col] = df[col].fillna(0)
            
        df['VWAP'] = np.where(df['VWAP'] == 0, df['close'], df['VWAP'])

        # 5. Market Structure & Institutional Features
        # Fair Value Gaps (FVG)
        df['FVG_Bullish'] = ((df['low'] > df['high'].shift(2)) & (df['close'].shift(1) > df['open'].shift(1))).astype(int)
        df['FVG_Bearish'] = ((df['high'] < df['low'].shift(2)) & (df['close'].shift(1) < df['open'].shift(1))).astype(int)
        
        # Simple Order Blocks
        df['Bullish_OB'] = ((df['close'].shift(1) < df['open'].shift(1)) & (df['close'] > df['open']) & (df['close'] > df['high'].shift(1))).astype(int)
        df['Bearish_OB'] = ((df['close'].shift(1) > df['open'].shift(1)) & (df['close'] < df['open']) & (df['close'] < df['low'].shift(1))).astype(int)

        # Support & Resistance (rolling 20 min/max)
        df['Support_20'] = df['low'].rolling(20).min()
        df['Resistance_20'] = df['high'].rolling(20).max()
        
        # Swing High/Low (3 bar fractal)
        df['Swing_High'] = ((df['high'].shift(1) > df['high']) & (df['high'].shift(1) > df['high'].shift(2))).astype(int)
        df['Swing_Low'] = ((df['low'].shift(1) < df['low']) & (df['low'].shift(1) < df['low'].shift(2))).astype(int)
        
        # Liquidity Sweeps
        df['Liq_Sweep_High'] = ((df['high'] > df['Resistance_20'].shift(1)) & (df['close'] < df['Resistance_20'].shift(1))).astype(int)
        df['Liq_Sweep_Low'] = ((df['low'] < df['Support_20'].shift(1)) & (df['close'] > df['Support_20'].shift(1))).astype(int)

        # Basic Market Structure (CHOCH/BOS)
        df['BOS_Bullish'] = ((df['close'] > df['Resistance_20'].shift(1))).astype(int)
        df['BOS_Bearish'] = ((df['close'] < df['Support_20'].shift(1))).astype(int)

        # 6. Session & Temporal
        if isinstance(df.index, pd.DatetimeIndex):
            df['Hour'] = df.index.hour
            df['DayOfWeek'] = df.index.dayofweek
            df['Month'] = df.index.month
            df['Quarter'] = df.index.quarter
            # Simplified sessions
            df['Session_Asian'] = ((df['Hour'] >= 0) & (df['Hour'] < 8)).astype(int)
            df['Session_London'] = ((df['Hour'] >= 8) & (df['Hour'] < 16)).astype(int)
            df['Session_NY'] = ((df['Hour'] >= 13) & (df['Hour'] < 21)).astype(int)

        # 7. Market Regime
        df['Regime'] = 0
        df.loc[(df['ADX'] > 25) & (df['DI_plus'] > df['DI_minus']), 'Regime'] = 1
        df.loc[(df['ADX'] > 25) & (df['DI_minus'] > df['DI_plus']), 'Regime'] = -1
        df.loc[df['ATR_14'] > df['ATR_14'].rolling(50).mean() * 1.5, 'Regime'] = 2

        # 8. Target Variable (for supervised training / evaluation)
        df['Future_Return_5'] = (df['close'].shift(-5) / df['close'] - 1.0).fillna(0.0)
        
        # Forward fill past values into future rows; never backward fill future values into past rows
        df.ffill(inplace=True)
        df.fillna(0.0, inplace=True)
        return df
