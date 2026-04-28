import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import config
import handlers  # регистрация хендлеров
from rating import load_rating, save_rating

# Здесь rating data подгружается при старте (для модуля rating)
load_rating()

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Экспортируем для handlers
__all__ = ['bot', 'dp']

async def main():
    print("🃏 КАРТОЧНЫЙ ДОМИК запущен!")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    asyncio.run(main())
