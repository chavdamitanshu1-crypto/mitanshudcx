import asyncio
import aiohttp
import pandas as pd
import logging
import time
from datetime import datetime

from config import *
from indicators import (
    calculate_indicators,
    check_long_signal,
    check_short_signal,
    get_trend_direction
)

from telegram_bot import send_telegram_alert, BOT_STATE

logger = logging.getLogger(__name__)


class FuturesScanner:
    def __init__(self):
        self.last_alerts = {}
        self.session = None

    async def init_session(self):
        self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()

    async def fetch_ticker_data(self):
        try:
            async with self.session.get("https://api.coindcx.com/exchange/ticker") as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception as e:
            logger.error(f"Ticker fetch error: {e}")
            return []

    async def fetch_active_pairs(self):
        try:
            async with self.session.get(FUTURES_INSTRUMENTS_URL) as resp:
                if resp.status != 200:
                    return []
                instruments = await resp.json()

            usdt_pairs = [p for p in instruments if isinstance(p, str) and p.endswith('_USDT')]

            tickers = await self.fetch_ticker_data()
            ticker_dict = {item.get('market'): item for item in tickers if isinstance(item, dict)}

            filtered_pairs = []
            for pair in usdt_pairs:
                ticker = ticker_dict.get(pair)
                if ticker and isinstance(ticker.get('volume'), (int, float)):
                    if float(ticker['volume']) > MIN_VOLUME_24H_USD:
                        filtered_pairs.append(pair)
                else:
                    filtered_pairs.append(pair)

            logger.info(f"Filtered to {len(filtered_pairs)} high-volume pairs")
            return filtered_pairs

        except Exception as e:
            logger.error(f"Error fetching pairs: {e}")
            return []

    async def fetch_candles(self, pair: str, interval: str, limit: int = 300):
        params = {"pair": pair, "interval": interval, "limit": limit}
        try:
            async with self.session.get(BASE_URL, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if not data:
                        return None

                    df = pd.DataFrame(data)
                    df = df[::-1].reset_index(drop=True)

                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')

                    if 'time' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['time'], unit='ms')

                    return df
                return None

        except Exception:
            return None

    async def get_multi_tf_trends(self, pair: str):
        trends = {}

        for tf in MULTI_TF:
            df = await self.fetch_candles(pair, tf, limit=250)

            if df is not None and len(df) >= TREND_SMA_PERIOD + 10:
                trends[tf] = get_trend_direction(df)
            else:
                trends[tf] = "Neutral (No Data)"

        return trends

    def should_alert(self, pair: str):
        now = time.time()

        if pair in self.last_alerts and now - self.last_alerts[pair] < ALERT_COOLDOWN:
            return False

        self.last_alerts[pair] = now
        return True

    async def process_pair(self, pair: str, alert_messages: list):
        for tf in TIMEFRAMES:
            df = await self.fetch_candles(pair, tf)

            if df is None or len(df) < SMA_PERIOD + 5:
                continue

            sma200, prev_sma, avg_vol, curr_vol = calculate_indicators(df)

            if sma200 is None:
                continue

            curr_close = df['close'].iloc[-1]
            prev_close = df['close'].iloc[-2]

            price_str = f"{curr_close:.6f}"
            sma_str = f"{sma200:.6f}"

            signal_type = None

            if check_long_signal(prev_close, curr_close, sma200, prev_sma, curr_vol, avg_vol):
                signal_type = "🚀 LONG SIGNAL"

            elif check_short_signal(prev_close, curr_close, sma200, prev_sma, curr_vol, avg_vol):
                signal_type = "🔻 SHORT SIGNAL"

            if signal_type and self.should_alert(pair):
                trends = await self.get_multi_tf_trends(pair)

                trend_summary = "\n".join(
                    [f"   {tf.upper()}: {trends.get(tf, 'No Data')}" for tf in MULTI_TF]
                )

                alert = f"""<b>{signal_type}</b>
Pair: <b>{pair}</b>
TF: {tf}
Price: {price_str}
SMA200: {sma_str}

Multi-TF Trend:
{trend_summary}
────────────────────"""

                alert_messages.append(alert)
                logger.info(f"{signal_type} → {pair} on {tf}")
                break

    async def scan_loop(self):
        while True:

            # ⛔ STOP / START CONTROL
            if not BOT_STATE.get("running", False):
                logger.info("⏸ Bot paused (waiting for START command)")
                await asyncio.sleep(5)
                continue

            start = time.time()
            pairs = await self.fetch_active_pairs()

            alert_messages = []

            tasks = [
                self.process_pair(pair, alert_messages)
                for pair in pairs
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

            if alert_messages:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                header = f"<b>🔔 CoinDCX Scanner</b>\nTime: {timestamp}\n\n"

                full_message = header + "\n\n".join(alert_messages)

                if len(full_message) > 3900:
                    full_message = full_message[:3900]

                await send_telegram_alert(full_message)

            elapsed = time.time() - start
            logger.info(f"Scan cycle done in {elapsed:.1f}s")

            await asyncio.sleep(30)