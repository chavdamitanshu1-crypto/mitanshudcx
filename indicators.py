import pandas as pd
from config import SMA_PERIOD, TREND_SMA_PERIOD, PRICE_BUFFER_PCT

def calculate_indicators(df: pd.DataFrame):
    if len(df) < SMA_PERIOD + 10:
        return None, None, None, None
    
    df['sma200'] = df['close'].rolling(window=SMA_PERIOD).mean()
    
    current_sma = df['sma200'].iloc[-1]
    prev_sma = df['sma200'].iloc[-2] if len(df) > SMA_PERIOD else current_sma
    
    curr_vol = df['volume'].iloc[-1]
    avg_vol = df['volume'].rolling(window=20).mean().iloc[-1]
    
    return current_sma, prev_sma, avg_vol, curr_vol


def check_long_signal(prev_close, curr_close, sma200, prev_sma, curr_vol, avg_vol):
    if pd.isna(sma200) or pd.isna(prev_sma):
        return False
    # Very relaxed for testing
    return (prev_close < sma200 and curr_close > sma200)


def check_short_signal(prev_close, curr_close, sma200, prev_sma, curr_vol, avg_vol):
    if pd.isna(sma200) or pd.isna(prev_sma):
        return False
    # Very relaxed for testing
    return (prev_close > sma200 and curr_close < sma200)


def get_trend_direction(df: pd.DataFrame, sma_period: int = TREND_SMA_PERIOD):
    if len(df) < sma_period + 10:
        return "Neutral (Insufficient Data)"
    
    df['sma'] = df['close'].rolling(window=sma_period).mean()
    current_price = df['close'].iloc[-1]
    sma_value = df['sma'].iloc[-1]
    
    if pd.isna(sma_value):
        return "Neutral"
    
    if current_price > sma_value * 1.001:
        return "🟢 Bullish"
    elif current_price < sma_value * 0.999:
        return "🔴 Bearish"
    else:
        return "⚪ Neutral"