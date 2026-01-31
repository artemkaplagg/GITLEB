# 🎰 Casino Bot Configuration

# Ваш Telegram Bot Token (от @BotFather)

TELEGRAM_TOKEN = “8570911226:AAEfa7tZquibcUh8HzCOrxZBQ-a5vwH84kA”

# Стартовый баланс для новых игроков (в 🪙)

STARTING_BALANCE = 17777

# Размеры доступных ставок

AVAILABLE_BETS = [10, 50, 100, 500, 1000]

# Множители выигрыша для каждой игры

GAME_MULTIPLIERS = {
“slots”: {
“jackpot”: 10,      # 64 значение (редко)
“big_win”: 5,       # 50-63
“win”: 2,           # 35-49
“small_win”: 1,     # 20-34
“lose”: 0,          # 0-19
},
“dice”: {
“6”: 6,             # Бросок кубика
“5”: 4,
“4”: 2,
“3”: 1,
“2”: 0,
“1”: 0,
},
“dart”: {
“6”: 8,             # Идеальные дартсы
“5”: 4,
“4”: 2,
“3”: 2,
“2”: 1,
“1”: 0,
},
“basketball”: {
“5”: 6,             # Идеальный бросок
“4”: 4,
“3”: 2,
“2”: 1,
“1”: 0,
}
}

# Сохраняет ли бот историю игр

SAVE_HISTORY = True

# Файл для сохранения данных пользователей

USERS_DATA_FILE = “users_balance.json”

# Игры доступные пользователям

AVAILABLE_GAMES = [“slots”, “dice”, “dart”, “basketball”]

# Логирование в файл

LOG_TO_FILE = True
LOG_FILE = “casino_bot.log”
