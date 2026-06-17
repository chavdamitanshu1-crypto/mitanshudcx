import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Config
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# CoinDCX Settings
BASE_URL = "https://public.coindcx.com/market_data/candles"
FUTURES_INSTRUMENTS_URL = "https://api.coindcx.com/exchange/v1/derivatives/futures/data/active_instruments"

# Scanner Settings
TIMEFRAMES = ['1m', '5m']
MIN_VOLUME_24H_USD = 15_000_000
SMA_PERIOD = 200
# VOLUME_MULTIPLIER = 1.5     # ← Removed
PRICE_BUFFER_PCT = 0.001

# Multi-Timeframe
MULTI_TF = ['1m', '5m', '15m', '1h', '4h']
TREND_SMA_PERIOD = 200

# Alert Cooldown
ALERT_COOLDOWN = 300

# Logging
LOG_LEVEL = "INFO"
BOT_RUNNING = False