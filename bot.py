# Rexbots
# Don't Remove Credit
# Telegram Channel @RexBots_Official

import os
import asyncio
import threading
import datetime
import sys
from datetime import timezone, timedelta
import aiohttp
from pyrogram import Client, filters, __version__ as pyrogram_version
from config import API_ID, API_HASH, BOT_TOKEN, KEEP_ALIVE_URL
from logger import LOGGER

logger = LOGGER(__name__)

# ✅ Indian Standard Time
IST = timezone(timedelta(hours=5, minutes=30))


async def keep_alive():
    """Send a request every 100 seconds to keep the bot alive."""
    logger.info(f"KEEP_ALIVE_URL set to: {KEEP_ALIVE_URL}")
    async with aiohttp.ClientSession() as session:
        while True:
            if KEEP_ALIVE_URL:
                try:
                    logger.info("Sending keep-alive request to keep the web app alive.")
                    await session.get(KEEP_ALIVE_URL)
                    logger.info("Sent keep-alive request successfully.")
                except Exception as e:
                    logger.error(f"Keep-alive request failed: {type(e).__name__}: {e}")
            await asyncio.sleep(100)


class Bot(Client):
    def __init__(self):
        super().__init__(
            "Rexbots Login",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="Rexbots"),
            workers=50,
            sleep_threshold=10
        )

    async def start(self):
        await super().start()
        me = await self.get_me()

        # Start keep-alive
        self.keep_alive_task = asyncio.create_task(keep_alive())

        # Bot startup log
        now = datetime.datetime.now(IST)
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        logger.info(f"Bot Started Successfully")
        logger.info(f"Bot Powered By @{me.username}")
        logger.info(f"Python Version: {py_ver}")
        logger.info(f"Pyrogram Version: {pyrogram_version}")

    async def stop(self, *args):
        me = await self.get_me()

        # Stop keep-alive loop
        if self.keep_alive_task:
            self.keep_alive_task.cancel()
            try:
                await self.keep_alive_task
            except asyncio.CancelledError:
                pass

        await super().stop()
        logger.info(f"Bot @{me.username} Stopped - Bye")


def run_flask_app():
    """Run Flask app in a separate thread"""
    from app import app
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting Flask web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


def main():
    """Main entry point - runs both Flask and Telegram bot"""
    port = int(os.environ.get('PORT', 10000))
    
    logger.info(f"Render Port: {port}")
    logger.info("Starting Telegram Bot with Web Server...")
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    logger.info("Flask web server started in background")
    
    # Run the Telegram bot (this will block)
    BotInstance = Bot()
    BotInstance.run()
    

if __name__ == "__main__":
    main()


# Rexbots
# Don't Remove Credit 🥺
# Telegram Channel @RexBots_Official

# Rexbots
# Don't Remove Credit
# Telegram Channel @RexBots_Official
