import asyncio
import logging
from config import load_config
from database.connection import init_db
from bot.setup import create_bot, create_dispatcher

async def start_bot():
    # 1. Load configuration
    cfg = load_config()

    # 2. Setup logging
    logging.basicConfig(
        level=getattr(logging, cfg.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    log = logging.getLogger("main")
    
    log.info("Starting bot in long-polling mode...")

    # 3. Initialize database (run migrations)
    await init_db()

    # 4. Create Bot and Dispatcher
    bot = create_bot(cfg)
    dp = create_dispatcher()

    # 5. Start polling
    try:
        # Get bot info to verify connection
        me = await bot.get_me()
        log.info(f"Bot @{me.username} (id={me.id}) is starting...")
        
        await dp.start_polling(bot)
    except Exception as e:
        log.exception(f"Critical error: {e}")
    finally:
        await bot.session.close()

def main():
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
