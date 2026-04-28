import asyncio
import sys
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import config
from rating import load_rating

# Включаем логирование всего
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Загружаем рейтинг
load_rating()

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Пытаемся импортировать handlers
try:
    import handlers
    logger.info("handlers imported successfully")
except Exception as e:
    logger.exception("FAILED to import handlers")
    sys.exit(1)

# Проверяем, зарегистрированы ли хендлеры
msg_handlers = len(dp.message.handlers)
cb_handlers = len(dp.callback_query.handlers)
print(f"Registered message handlers: {msg_handlers}")
print(f"Registered callback query handlers: {cb_handlers}")

if msg_handlers == 0 and cb_handlers == 0:
    print("WARNING: No handlers registered! Check handlers.py for errors.")
    # Не выходим, но предупреждаем

async def main():
    print("🃏 КАРТОЧНЫЙ ДОМИК запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except Exception as e:
        logger.exception("Polling crashed")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())