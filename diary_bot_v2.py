import json
import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.error import TelegramError

# ================== LOGGING ==================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================== CONFIG ==================

TOKEN = os.getenv("TELEGRAM_TOKEN", "8570911226:AAEfa7tZquibcUh8HzCOrxZBQ-a5vwH84kA")

USERS_FILE = "users.json"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE_PATH = DATA_DIR / USERS_FILE

# Images
IMG_MAIN_MENU = "https://i.ibb.co/1sKjVzT/main-menu.jpg"
IMG_LOGIN = "https://i.ibb.co/0jQY0hH/login.jpg"
IMG_CONNECT = "https://i.ibb.co/4YgK8Rg/connect.jpg"

# States
(
    ASK_NAME,
    ASK_AGE,
    ASK_GOAL,
) = range(3)

MAIN_MENU = 10

# Keyboard layouts
MAIN_KEYBOARD = [
    ["📝 Новая запись"],
    ["📊 Статистика", "📖 История"],
    ["❌ Выход"],
]

# ================== STORAGE ==================

class UserStorage:
    """Управление хранилищем пользователей"""

    @staticmethod
    def load_users() -> Dict[str, Dict[str, Any]]:
        """Загрузить пользователей из файла"""
        try:
            if USERS_FILE_PATH.exists():
                with open(USERS_FILE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Ошибка при загрузке пользователей: {e}")
        return {}

    @staticmethod
    def save_users(data: Dict[str, Dict[str, Any]]) -> bool:
        """Сохранить пользователей в файл"""
        try:
            with open(USERS_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            logger.error(f"Ошибка при сохранении пользователей: {e}")
            return False

    @staticmethod
    def user_exists(user_id: str) -> bool:
        """Проверить существование пользователя"""
        return user_id in UserStorage.load_users()

    @staticmethod
    def get_user(user_id: str) -> Dict[str, Any] | None:
        """Получить данные пользователя"""
        users = UserStorage.load_users()
        return users.get(user_id)

    @staticmethod
    def save_user(user_id: str, user_data: Dict[str, Any]) -> bool:
        """Сохранить данные пользователя"""
        users = UserStorage.load_users()
        users[user_id] = user_data
        return UserStorage.save_users(users)


# ================== MESSAGE TEMPLATES ==================

class Messages:
    """Шаблоны сообщений"""

    REGISTRATION_WELCOME = (
        "ВХОД В КАБИНЕТ\n\n"
        "Чтобы продолжить, нужно зарегистрироваться.\n\n"
        "Введите ваше имя:"
    )

    ASK_AGE = "Введите ваш возраст:"

    ASK_GOAL = (
        "Ваша главная цель?\n\n"
        "Пример: дисциплина, учёба, здоровье"
    )

    INVALID_AGE = "Введите корректный возраст (число)."

    CONNECTING = "Подключение...\nПожалуйста, подождите"

    MAIN_MENU_CAPTION = "Главное меню\nВыберите действие"

    NEW_RECORD = "📝 Функция создания записи в разработке."
    STATISTICS = "📊 Скоро будет красивая статистика."
    HISTORY = "📖 История пока пуста."

    LOGOUT = "Вы вышли.\nВведите /start чтобы вернуться."

    INVALID_MENU = "Выберите пункт меню."

    ERROR = "Произошла ошибка. Попробуйте позже или введите /start"


# ================== HANDLERS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    try:
        user_id = str(update.effective_user.id)

        # Очищаем старые данные
        context.user_data.clear()
        
        # Если пользователь уже зарегистрирован
        if UserStorage.user_exists(user_id):
            return await show_main_menu(update, context)
        
        # Новый пользователь - начинаем регистрацию
        msg = await update.message.reply_photo(
            photo=IMG_LOGIN,
            caption=Messages.REGISTRATION_WELCOME,
        )
        
        context.user_data["register_message_id"] = msg.message_id
        context.user_data["registration_started"] = True
        return ASK_NAME
        
    except TelegramError as e:
        logger.error(f"Ошибка Telegram при /start: {e}")
        await update.message.reply_text(Messages.ERROR)
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Неожиданная ошибка в start: {e}")
        await update.message.reply_text(Messages.ERROR)
        return ConversationHandler.END


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода имени"""
    try:
        # Удаляем фото регистрации
        if "register_message_id" in context.user_data:
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=context.user_data["register_message_id"],
                )
                del context.user_data["register_message_id"]
            except TelegramError as e:
                logger.warning(f"Не удалось удалить сообщение регистрации: {e}")
        
        name = update.message.text.strip()

        if not name or len(name) < 2:
            await update.message.reply_text("Введите корректное имя (минимум 2 символа).")
            return ASK_NAME

        context.user_data["name"] = name
        await update.message.reply_text(Messages.ASK_AGE)
        return ASK_AGE

    except Exception as e:
        logger.error(f"Ошибка в ask_name: {e}")
        await update.message.reply_text(Messages.ERROR)
        return ConversationHandler.END


async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода возраста"""
    try:
        age_text = update.message.text.strip()

        if not age_text.isdigit():
            await update.message.reply_text(Messages.INVALID_AGE)
            return ASK_AGE

        age = int(age_text)

        if age < 1 or age > 150:
            await update.message.reply_text("Введите реалистичный возраст (1-150).")
            return ASK_AGE

        context.user_data["age"] = age
        await update.message.reply_text(Messages.ASK_GOAL)
        return ASK_GOAL

    except Exception as e:
        logger.error(f"Ошибка в ask_age: {e}")
        await update.message.reply_text(Messages.ERROR)
        return ConversationHandler.END


async def ask_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода цели"""
    try:
        user_id = str(update.effective_user.id)
        goal = update.message.text.strip()

        if not goal or len(goal) < 3:
            await update.message.reply_text("Введите корректную цель (минимум 3 символа).")
            return ASK_GOAL

        # Сохраняем данные пользователя
        user_data = {
            "name": context.user_data["name"],
            "age": context.user_data["age"],
            "goal": goal,
        }

        if not UserStorage.save_user(user_id, user_data):
            await update.message.reply_text(Messages.ERROR)
            return ConversationHandler.END

        # Экран подключения
        connect_msg = await update.message.reply_photo(
            photo=IMG_CONNECT,
            caption=Messages.CONNECTING
        )

        await asyncio.sleep(3)

        # Удаляем сообщение подключения
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=connect_msg.message_id,
            )
        except TelegramError as e:
            logger.warning(f"Не удалось удалить сообщение подключения: {e}")

        # Очищаем временные данные
        if "registration_started" in context.user_data:
            del context.user_data["registration_started"]
            
        return await show_main_menu(update, context)

    except Exception as e:
        logger.error(f"Ошибка в ask_goal: {e}")
        await update.message.reply_text(Messages.ERROR)
        return ConversationHandler.END


# ================== MAIN MENU ==================

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню"""
    try:
        # Проверяем, есть ли сообщение для ответа (update.message может отсутствовать при вызове из ask_goal)
        if update.message:
            await update.message.reply_photo(
                photo=IMG_MAIN_MENU,
                caption=Messages.MAIN_MENU_CAPTION,
                reply_markup=ReplyKeyboardMarkup(MAIN_KEYBOARD, resize_keyboard=True),
            )
        else:
            # Если вызывается из ask_goal, используем context для отправки
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=IMG_MAIN_MENU,
                caption=Messages.MAIN_MENU_CAPTION,
                reply_markup=ReplyKeyboardMarkup(MAIN_KEYBOARD, resize_keyboard=True),
            )
        return MAIN_MENU

    except TelegramError as e:
        logger.error(f"Ошибка при показе меню: {e}")
        # Если не удалось отправить фото, отправляем текстовое меню
        if update.message:
            await update.message.reply_text(
                Messages.MAIN_MENU_CAPTION,
                reply_markup=ReplyKeyboardMarkup(MAIN_KEYBOARD, resize_keyboard=True),
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=Messages.MAIN_MENU_CAPTION,
                reply_markup=ReplyKeyboardMarkup(MAIN_KEYBOARD, resize_keyboard=True),
            )
        return MAIN_MENU
    except Exception as e:
        logger.error(f"Неожиданная ошибка в show_main_menu: {e}")
        if update.message:
            await update.message.reply_text(Messages.ERROR)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=Messages.ERROR,
            )
        return ConversationHandler.END


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик меню"""
    try:
        text = update.message.text.strip()

        menu_handlers = {
            "📝 Новая запись": Messages.NEW_RECORD,
            "📊 Статистика": Messages.STATISTICS,
            "📖 История": Messages.HISTORY,
        }

        if text in menu_handlers:
            await update.message.reply_text(menu_handlers[text])
            return MAIN_MENU

        elif text == "❌ Выход":
            await update.message.reply_text(
                Messages.LOGOUT,
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END

        else:
            await update.message.reply_text(Messages.INVALID_MENU)
            return MAIN_MENU

    except TelegramError as e:
        logger.error(f"Ошибка Telegram в handle_menu: {e}")
        await update.message.reply_text(Messages.ERROR)
        return MAIN_MENU
    except Exception as e:
        logger.error(f"Ошибка в handle_menu: {e}")
        await update.message.reply_text(Messages.ERROR)
        return MAIN_MENU


# ================== MAIN ==================

def main():
    """Запуск бота"""
    try:
        if TOKEN == "PASTE_YOUR_TOKEN_HERE":
            raise ValueError("Установите корректный токен в TOKEN или переменной TELEGRAM_TOKEN")

        app = Application.builder().token(TOKEN).build()

        conv = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
                ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_age)],
                ASK_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_goal)],
                MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
            },
            fallbacks=[CommandHandler("start", start)],
        )

        app.add_handler(conv)

        logger.info("🤖 Бот запущен и готов к работе")
        app.run_polling(allowed_updates=Update.ALL_TYPES)

    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        raise
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    main()
