import aiohttp
import asyncio
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

# ================= BOT STATE =================
BOT_STATE = {
    "running": False
}

last_update_id = 0


# ================= SEND MESSAGE =================
async def send_telegram_alert(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            return await resp.text()


# ================= LISTEN TELEGRAM COMMANDS =================
async def listen_telegram_commands():
    """
    Poll Telegram for messages: start / exit
    """

    global last_update_id

    if not TELEGRAM_BOT_TOKEN:
        logger.error("Telegram token missing!")
        return

    offset = last_update_id

    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {"timeout": 10, "offset": offset + 1}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()

            for result in data.get("result", []):
                offset = result["update_id"]

                if "message" not in result:
                    continue

                text = result["message"].get("text", "").lower()

                if text == "start":
                    BOT_STATE["running"] = True
                    await send_telegram_alert("🚀 Scanner STARTED")

                elif text == "exit":
                    BOT_STATE["running"] = False
                    await send_telegram_alert("⛔ Scanner STOPPED")

        except Exception as e:
            logger.error(f"Telegram listener error: {e}")

        await asyncio.sleep(3)