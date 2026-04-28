import asyncio
import sys
import logging
from aiogram.fsm.storage.memory import MemoryStorage
import config
from rating import load_rating
from dispatcher import bot, dp  # теперь bot и dp из отдельного модуля

# Убираем лишние импорты config и rating, если они не нужны
load_rating()

# Настройка логирования
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Импортируем handlers без цикла
import handlers

# Проверяем количество хендлеров
print(f"Registered message handlers: {len(dp.message.handlers)}")
print(f"Registered callback query handlers: {len(dp.callback_query.handlers)}")

async def main():
    print("🃏 КАРТОЧНЫЙ ДОМИК запущен!")
    # Обязательно удаляем вебхук и сбрасываем pending updates
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
