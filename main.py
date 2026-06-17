import asyncio
import logging
from scanner import FuturesScanner
from config import LOG_LEVEL
from telegram_bot import send_telegram_alert, listen_telegram_commands

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    scanner = FuturesScanner()
    await scanner.init_session()

    try:
        logger = logging.getLogger(__name__)
        logger.info("🚀 Bot starting...")

        await send_telegram_alert(
            "🤖 Bot ONLINE\nSend 'start' to begin scanning\nSend 'exit' to stop scanning"
        )

        # 🔥 RUN BOTH TASKS TOGETHER
        await asyncio.gather(
            scanner.scan_loop(),
            listen_telegram_commands()
        )

    except Exception as e:
        logger.error(f"Error: {e}")

    finally:
        await scanner.close()


if __name__ == "__main__":
    asyncio.run(main())