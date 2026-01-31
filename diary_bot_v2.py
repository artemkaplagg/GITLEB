#!/usr/bin/env python3
"""
Casino Bot для Telegram
Використовує токен з файлу config.py
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import DiceEmoji
import json
from pathlib import Path

# --- ІМПОРТ ТОКЕНА ---
try:
    from config import TOKEN
except ImportError:
    print("❌ Помилка: Файл config.py не знайдено або в ньому немає змінної TOKEN!")
    print("Створи файл config.py і напиши туди: TOKEN = 'твій_токен'")
    exit()

# Логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Файл для збереження балансу
USERS_FILE = "users_balance.json"

class CasinoBot:
    def __init__(self):
        self.users = self.load_users()
        self.games_config = {
            "slots": {"emoji": "🎰", "name": "Слоти", "cost": 10},
            "dice": {"emoji": "🎲", "name": "Кубик", "cost": 10},
            "dart": {"emoji": "🎯", "name": "Дартс", "cost": 10},
            "basketball": {"emoji": "🏀", "name": "Баскетбол", "cost": 10},
        }

    def load_users(self):
        """Завантажує баланс з файлу"""
        if Path(USERS_FILE).exists():
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_users(self):
        """Зберігає баланс у файл"""
        with open(USERS_FILE, 'w') as f:
            json.dump(self.users, f, indent=2)

    def get_user_balance(self, user_id: int) -> int:
        user_id_str = str(user_id)
        if user_id_str not in self.users:
            self.users[user_id_str] = {"balance": 1000, "total_wins": 0, "total_spent": 0}
            self.save_users()
        return self.users[user_id_str]["balance"]

    def update_balance(self, user_id: int, amount: int):
        user_id_str = str(user_id)
        if user_id_str not in self.users:
            self.get_user_balance(user_id)
        
        self.users[user_id_str]["balance"] += amount
        if amount > 0:
            self.users[user_id_str]["total_wins"] += amount
        else:
            self.users[user_id_str]["total_spent"] += abs(amount)
        self.save_users()

    def get_main_menu(self) -> InlineKeyboardMarkup:
        buttons = [
            [
                InlineKeyboardButton("🎰 Слоти", callback_data="game_slots"),
                InlineKeyboardButton("🎲 Кубик", callback_data="game_dice"),
            ],
            [
                InlineKeyboardButton("🎯 Дартс", callback_data="game_dart"),
                InlineKeyboardButton("🏀 Баскетбол", callback_data="game_basketball"),
            ],
            [
                InlineKeyboardButton("💰 Баланс", callback_data="balance"),
                InlineKeyboardButton("📊 Статистика", callback_data="stats"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)

    def get_bet_menu(self, game: str) -> InlineKeyboardMarkup:
        buttons = [
            [
                InlineKeyboardButton("10 🪙", callback_data=f"bet_10_{game}"),
                InlineKeyboardButton("50 🪙", callback_data=f"bet_50_{game}"),
                InlineKeyboardButton("100 🪙", callback_data=f"bet_100_{game}"),
            ],
            [
                InlineKeyboardButton("500 🪙", callback_data=f"bet_500_{game}"),
                InlineKeyboardButton("1000 🪙", callback_data=f"bet_1000_{game}"),
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back")],
        ]
        return InlineKeyboardMarkup(buttons)

# Ініціалізація
casino = CasinoBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    casino.get_user_balance(user_id)

    welcome_text = (
        f"🎰 **Ласкаво просимо в Casino Bot!** 🎰\n\n"
        f"Твій стартовий капітал: **1000 🪙**\n"
        f"Обирай гру та піднімай бабло!"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=casino.get_main_menu(),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    current_balance = casino.get_user_balance(user_id)
    data = query.data

    if data == "back":
        await query.edit_message_text(
            text="🎰 **Обери гру:**",
            reply_markup=casino.get_main_menu(),
            parse_mode="Markdown"
        )
        return

    if data == "balance":
        await query.edit_message_text(
            text=f"💰 **Твій баланс: {current_balance} 🪙**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]),
            parse_mode="Markdown"
        )
        return

    if data == "stats":
        user_data = casino.users[str(user_id)]
        stats_text = (
            f"📊 **Статистика:**\n"
            f"💰 Баланс: {user_data['balance']} 🪙\n"
            f"✅ Виграно: {user_data['total_wins']} 🪙\n"
            f"❌ Програно: {user_data['total_spent']} 🪙"
        )
        await query.edit_message_text(
            text=stats_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]),
            parse_mode="Markdown"
        )
        return

    if data.startswith("game_"):
        game = data.split("_")[1]
        game_info = casino.games_config[game]
        text = f"{game_info['emoji']} **{game_info['name']}**\n\nСкільки ставиш?"
        await query.edit_message_text(
            text=text,
            reply_markup=casino.get_bet_menu(game),
            parse_mode="Markdown"
        )
        return

    if data.startswith("bet_"):
        parts = data.split("_")
        bet_amount = int(parts[1])
        game = parts[2]

        if current_balance < bet_amount:
            await query.answer("❌ Немає грошей, бомж!", show_alert=True)
            return

        # Списуємо ставку
        casino.update_balance(user_id, -bet_amount)

        # Кидаємо дайс
        emoji_map = {
            "slots": DiceEmoji.SLOT_MACHINE,
            "dice": DiceEmoji.DICE,
            "dart": DiceEmoji.DARTS,
            "basketball": DiceEmoji.BASKETBALL
        }
        
        sent_message = await context.bot.send_dice(
            chat_id=query.message.chat_id,
            emoji=emoji_map[game],
            reply_to_message_id=query.message.message_id
        )

        # Передаємо дані в обробку результату
        await process_result(update, sent_message.dice.value, sent_message.dice.emoji, user_id, bet_amount, game)

async def process_result(update: Update, value: int, emoji: str, user_id: int, bet: int, game_key: str):
    """Рахуємо виграш"""
    winnings = 0
    text = ""

    # Логіка виграшів
    if emoji == DiceEmoji.SLOT_MACHINE:
        if value == 64: # Джекпот
            winnings = bet * 10
            text = "🏆 **ДЖЕКПОТ!!!**"
        elif value in [1, 22, 43]: # Три сімки/бари (приблизно)
            winnings = bet * 5
            text = "🎉 **БІГ ВІН!**"
        elif value % 4 == 0: # Маленький виграш
            winnings = bet * 2
            text = "✅ **Плюс!**"
        else:
            text = "❌ **Мимо**"

    elif emoji == DiceEmoji.DICE:
        if value == 6:
            winnings = bet * 5
            text = "🏆 **ТОП!**"
        elif value >= 4:
            winnings = bet * 2
            text = "✅ **Виграв**"
        else:
            text = "❌ **Програв**"
    
    elif emoji == DiceEmoji.DARTS:
        if value == 6:
            winnings = bet * 5
            text = "🎯 **В ЦЕНТР!**"
        elif value >= 4:
            winnings = bet * 2
            text = "✅ **Норм**"
        else:
            text = "❌ **Мазила**"

    elif emoji == DiceEmoji.BASKETBALL:
        if value >= 4:
            winnings = bet * 3
            text = "🏀 **ГОЛ!**"
        else:
            text = "❌ **Штанга**"

    # Нарахування
    if winnings > 0:
        casino.update_balance(user_id, winnings)
        text += f"\n💰 +{winnings} 🪙"
    else:
        text += f"\n💸 -{bet} 🪙"

    new_bal = casino.get_user_balance(user_id)
    text += f"\n💵 Баланс: {new_bal}"

    buttons = [
        [InlineKeyboardButton("🎮 Ще раз", callback_data=f"game_{game_key}")],
        [InlineKeyboardButton("🏠 Меню", callback_data="back")],
    ]

    # Відправляємо нове повідомлення з результатом
    if update.callback_query and update.callback_query.message:
         await update.callback_query.message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )

def main():
    # Токен береться з імпорту зверху
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print(f"✅ Бот запущено! (Токен з config.py)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
