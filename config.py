BOT_TOKEN = "8716737570:AAF6_1Qnbq3K9GqZBVtlEn6pmfYviQhOE0s"
ADMIN_ID = 6185367393
ONLINE_TIMEOUT = 30

SUITS = [
    {"sym": "♥️", "name": "Классические отжимания", "emoji": "💪", "tip": "Локти вдоль тела!"},
    {"sym": "♠️", "name": "Широкий хват",           "emoji": "🦅", "tip": "Руки шире плеч!"},
    {"sym": "♦️", "name": "Алмазные (узкий хват)",  "emoji": "💎", "tip": "Руки ромбом!"},
    {"sym": "♣️", "name": "Взрывные (с хлопком)",   "emoji": "💥", "tip": "Взрывной толчок!"},
]

RANKS   = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
VALUES  = {str(i): i for i in range(2, 11)}
VALUES.update({"J": 12, "Q": 12, "K": 12, "A": 15})

RANK_DISPLAY = {
    **{str(i): str(i) for i in range(2, 11)},
    "J": "Валет 🎖",
    "Q": "Дама 👑",
    "K": "Король 🏆",
    "A": "ТУЗ ⚡",
}

MEDALS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"]

ACHIEVEMENTS = {
    "first_game":      {"name": "🔰 Новичок",        "desc": "Сыграть первую игру"},
    "first_win":       {"name": "🏆 Первая кровь",   "desc": "Одержать первую победу"},
    "five_wins":       {"name": "⚔️ Гладиатор",      "desc": "Выиграть 5 игр"},
    "hundred_pushups": {"name": "💯 Сотня",          "desc": "Сделать 100 отжиманий за игру"},
    "ten_rounds":      {"name": "🔥 Крепкий орешек", "desc": "Пережить 10 раундов в игре"},
}

WIN_REACTIONS = ["🔥", "💪", "👑", "⚡", "🎉", "🏆", "🥇", "💥"]

# Глобальное онлайн-лобби
online_lobby = None

from aiogram.fsm.state import State, StatesGroup

class Game(StatesGroup):
    naming  = State()
    playing = State()

class SettingsState(StatesGroup):
    waiting_timeout = State()

class TrainingState(StatesGroup):
    playing = State()
