import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import config
from rating import load_rating

# Загружаем рейтинг при старте
load_rating()

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())  # Это главный dp

# Импортируем handlers ПОСЛЕ создания dp
import handlers

async def main():
    print("🃏 КАРТОЧНЫЙ ДОМИК запущен!")
    # Удаляем вебхук на всякий случай и запускаем поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    asyncio.run(main())