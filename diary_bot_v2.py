#!/usr/bin/env python3
“””
Casino Bot для Telegram - использует встроенные игры ТГ
Автоматически обрабатывает результаты из Telegram Game API
“””

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import DiceEmoji
import json
from pathlib import Path

# Логирование

logging.basicConfig(
format=’%(asctime)s - %(name)s - %(levelname)s - %(message)s’,
level=logging.INFO
)
logger = logging.getLogger(**name**)

# Файл для сохранения баланса пользователей

USERS_FILE = “users_balance.json”

class CasinoBot:
def **init**(self):
self.users = self.load_users()
self.games_config = {
“slots”: {“emoji”: “🎰”, “name”: “Слоты”, “cost”: 10, “multiplier”: 0.95},
“dice”: {“emoji”: “🎲”, “name”: “Кубик”, “cost”: 10, “multiplier”: 0.95},
“dart”: {“emoji”: “🎯”, “name”: “Дартс”, “cost”: 10, “multiplier”: 0.95},
“basketball”: {“emoji”: “🏀”, “name”: “Баскетбол”, “cost”: 10, “multiplier”: 0.95},
}
self.winnings = {
“slots”: {
“🍒🍒🍒”: 100,
“🍋🍋🍋”: 150,
“🍓🍓🍓”: 200,
“🍌🍌🍌”: 120,
“⭐⭐⭐”: 300,
“🔔🔔🔔”: 250,
“💰💰💰”: 500,
“7️⃣7️⃣7️⃣”: 1000,
},
“dice”: {
6: 60,
5: 50,
4: 40,
3: 30,
2: 20,
1: 10,
}
}

```
def load_users(self):
    """Загружает баланс пользователей из файла"""
    if Path(USERS_FILE).exists():
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(self):
    """Сохраняет баланс пользователей"""
    with open(USERS_FILE, 'w') as f:
        json.dump(self.users, f, indent=2)

def get_user_balance(self, user_id: int) -> int:
    """Получает баланс пользователя"""
    user_id_str = str(user_id)
    if user_id_str not in self.users:
        self.users[user_id_str] = {"balance": 1000, "total_wins": 0, "total_spent": 0}
        self.save_users()
    return self.users[user_id_str]["balance"]

def update_balance(self, user_id: int, amount: int):
    """Обновляет баланс пользователя"""
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
    """Создает главное меню с кнопками игр"""
    buttons = [
        [
            InlineKeyboardButton("🎰 Слоты", callback_data="game_slots"),
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
    """Меню выбора ставки"""
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
```

# Инициализируем бота

casino = CasinoBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Стартовая команда”””
user_id = update.effective_user.id
casino.get_user_balance(user_id)

```
welcome_text = (
    f"🎰 **Добро пожаловать в Casino Bot!** 🎰\n\n"
    f"Начальный баланс: **1000 🪙**\n\n"
    f"Выбери игру и начни выигрывать!\n"
    f"Удачи, {update.effective_user.first_name}!"
)

await update.message.reply_text(
    welcome_text,
    reply_markup=casino.get_main_menu(),
    parse_mode="Markdown"
)
```

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Обработчик всех кнопок”””
query = update.callback_query
await query.answer()

```
user_id = query.from_user.id
current_balance = casino.get_user_balance(user_id)
data = query.data

# Команда: Назад в меню
if data == "back":
    await query.edit_message_text(
        text="🎰 **Выбери игру:**",
        reply_markup=casino.get_main_menu(),
        parse_mode="Markdown"
    )
    return

# Команда: Баланс
if data == "balance":
    balance_text = f"💰 **Твой баланс: {current_balance} 🪙**"
    await query.edit_message_text(
        text=balance_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]),
        parse_mode="Markdown"
    )
    return

# Команда: Статистика
if data == "stats":
    user_data = casino.users[str(user_id)]
    stats_text = (
        f"📊 **Твоя Статистика:**\n\n"
        f"💰 Текущий баланс: {user_data['balance']} 🪙\n"
        f"✅ Общие выигрыши: {user_data['total_wins']} 🪙\n"
        f"❌ Общие потери: {user_data['total_spent']} 🪙\n"
        f"📈 Баланс от начала: {user_data['balance'] - 1000 + user_data['total_spent']} 🪙"
    )
    await query.edit_message_text(
        text=stats_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]),
        parse_mode="Markdown"
    )
    return

# Выбор игры
if data.startswith("game_"):
    game = data.split("_")[1]
    game_name = casino.games_config[game]["name"]
    game_emoji = casino.games_config[game]["emoji"]
    
    text = f"{game_emoji} **{game_name}**\n\nВыбери размер ставки:"
    await query.edit_message_text(
        text=text,
        reply_markup=casino.get_bet_menu(game),
        parse_mode="Markdown"
    )
    return

# Выбор ставки и запуск игры
if data.startswith("bet_"):
    parts = data.split("_")
    bet_amount = int(parts[1])
    game = parts[2]

    # Проверка баланса
    if current_balance < bet_amount:
        await query.answer("❌ Недостаточно денег!", show_alert=True)
        return

    # Снимаем ставку
    casino.update_balance(user_id, -bet_amount)

    # Запускаем игру
    if game == "slots":
        await context.bot.send_dice(
            chat_id=query.message.chat_id,
            emoji=DiceEmoji.SLOT_MACHINE,
            reply_to_message_id=query.message.message_id
        )
        # Сохраняем информацию о текущей игре в контексте
        context.user_data['last_bet'] = bet_amount
        context.user_data['last_game'] = 'slots'

    elif game == "dice":
        await context.bot.send_dice(
            chat_id=query.message.chat_id,
            emoji=DiceEmoji.DICE,
            reply_to_message_id=query.message.message_id
        )
        context.user_data['last_bet'] = bet_amount
        context.user_data['last_game'] = 'dice'

    elif game == "dart":
        await context.bot.send_dice(
            chat_id=query.message.chat_id,
            emoji=DiceEmoji.DARTS,
            reply_to_message_id=query.message.message_id
        )
        context.user_data['last_bet'] = bet_amount
        context.user_data['last_game'] = 'dart'

    elif game == "basketball":
        await context.bot.send_dice(
            chat_id=query.message.chat_id,
            emoji=DiceEmoji.BASKETBALL,
            reply_to_message_id=query.message.message_id
        )
        context.user_data['last_bet'] = bet_amount
        context.user_data['last_game'] = 'basketball'

    await query.edit_message_text(
        text=f"🎮 Игра запущена!\n\nТвоя ставка: {bet_amount} 🪙",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="back")]])
    )
```

async def dice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Обработчик результатов игры”””
user_id = update.effective_user.id

```
if update.message.dice:
    dice_value = update.message.dice.value
    game_emoji = update.message.dice.emoji
    
    # Получаем информацию о последней ставке
    last_bet = context.user_data.get('last_bet', 0)
    last_game = context.user_data.get('last_game', '')

    # Определяем выигрыш в зависимости от типа игры
    winnings = 0

    if game_emoji == DiceEmoji.SLOT_MACHINE:
        # Для слотов ТГ возвращает значение 1-64 (8x8)
        # Каждое число соответствует комбинации символов
        if dice_value == 64:  # ТГ редко дает максимум
            winnings = last_bet * 10
            result_text = "🏆 **ДЖЕКПОТ!!!** 💰💰💰"
        elif dice_value >= 50:
            winnings = last_bet * 5
            result_text = "🎉 **Большой выигрыш!**"
        elif dice_value >= 35:
            winnings = last_bet * 2
            result_text = "✅ **Выигрыш!**"
        elif dice_value >= 20:
            winnings = last_bet
            result_text = "👍 **Небольшой выигрыш**"
        else:
            result_text = "❌ **Проигрыш**"

    elif game_emoji == DiceEmoji.DICE:
        # Кубик: 1-6
        if dice_value == 6:
            winnings = last_bet * 6
            result_text = "🏆 **КРИТИЧЕСКИЙ БРОСОК!** ⭐"
        elif dice_value == 5:
            winnings = last_bet * 4
            result_text = "🎉 **Отличный бросок!**"
        elif dice_value == 4:
            winnings = last_bet * 2
            result_text = "✅ **Выигрыш!**"
        elif dice_value == 3:
            winnings = last_bet
            result_text = "👍 **Небольшой выигрыш**"
        else:
            result_text = "❌ **Проигрыш**"

    elif game_emoji == DiceEmoji.DARTS:
        # Дартс: 1-6 (количество попаданий)
        if dice_value == 6:
            winnings = last_bet * 8
            result_text = "🏆 **ИДЕАЛЬНО!** 🎯🎯🎯"
        elif dice_value >= 5:
            winnings = last_bet * 4
            result_text = "🎉 **Почти идеально!**"
        elif dice_value >= 3:
            winnings = last_bet * 2
            result_text = "✅ **Хороший бросок!**"
        elif dice_value == 2:
            winnings = last_bet
            result_text = "👍 **Попали!**"
        else:
            result_text = "❌ **Промах**"

    elif game_emoji == DiceEmoji.BASKETBALL:
        # Баскетбол: 1-5
        if dice_value == 5:
            winnings = last_bet * 6
            result_text = "🏆 **БРОСОК С ЦЕНТРА ПЛОЩАДКИ!** 🏀🏀"
        elif dice_value == 4:
            winnings = last_bet * 4
            result_text = "🎉 **Отличный бросок!**"
        elif dice_value == 3:
            winnings = last_bet * 2
            result_text = "✅ **Попадание!**"
        elif dice_value == 2:
            winnings = last_bet
            result_text = "👍 **Забил!**"
        else:
            result_text = "❌ **Не забил**"

    else:
        result_text = "❓ Неизвестная игра"

    # Обновляем баланс
    if winnings > 0:
        casino.update_balance(user_id, winnings)
        current_balance = casino.get_user_balance(user_id)
        message_text = (
            f"{result_text}\n\n"
            f"🎯 Результат: **{dice_value}**\n"
            f"💰 Выигрыш: +{winnings} 🪙\n"
            f"💵 Новый баланс: {current_balance} 🪙"
        )
    else:
        current_balance = casino.get_user_balance(user_id)
        message_text = (
            f"{result_text}\n\n"
            f"🎯 Результат: **{dice_value}**\n"
            f"💸 Потеря: -{last_bet} 🪙\n"
            f"💵 Новый баланс: {current_balance} 🪙"
        )

    # Отправляем результат
    buttons = [
        [InlineKeyboardButton("🎮 Еще раз", callback_data=f"game_{last_game}")],
        [InlineKeyboardButton("🏠 Меню", callback_data="back")],
    ]
    
    await update.message.reply_text(
        text=message_text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )
```

def main():
“”“Главная функция”””
# Вставьте ваш токен здесь
TOKEN = “ВАШ_ТОКЕН_ТГ”

```
# Если токена нет, просим его ввести
if TOKEN == "ВАШ_ТОКЕН_ТГ":
    print("❌ Ошибка: укажите TOKEN в коде!")
    print("Получить токен: https://t.me/BotFather")
    return

# Создаем приложение
app = Application.builder().token(TOKEN).build()

# Обработчики
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.Dice(), dice_handler))

# Запускаем бота
print("✅ Casino Bot запущен!")
app.run_polling(allowed_updates=Update.ALL_TYPES)
```

if **name** == “**main**”:
main()