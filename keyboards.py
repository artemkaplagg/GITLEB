from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def kb_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️  Сразиться!", callback_data="battle", style="danger")],
        [InlineKeyboardButton(text="🏋️  Тренировка", callback_data="solo")],
        [InlineKeyboardButton(text="🌐  Онлайн",     callback_data="online", style="success")],
        [InlineKeyboardButton(text="📖  Правила",    callback_data="rules"),
         InlineKeyboardButton(text="🏆  Рейтинг",   callback_data="rating")],
    ])

def kb_player_count() -> InlineKeyboardMarkup:
    row = [InlineKeyboardButton(text=str(i), callback_data=f"n_{i}") for i in range(2, 7)]
    return InlineKeyboardMarkup(inline_keyboard=[
        row,
        [InlineKeyboardButton(text="❌ Отмена", callback_data="menu", style="danger")],
    ])

def kb_draw() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🃏  Тянуть карту!", callback_data="draw")],
        [InlineKeyboardButton(text="📊  Счёт",          callback_data="score"),
         InlineKeyboardButton(text="🏁  Завершить",     callback_data="finish", style="danger")],
        [InlineKeyboardButton(text="🏳  Сдаться",       callback_data="quit", style="primary")],
    ])

def kb_done() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅  Сделано!", callback_data="done", style="success")],
        [InlineKeyboardButton(text="🏳  Сдаться",  callback_data="quit", style="primary")],
    ])

def kb_end(players: list) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"🏆  {p['name']} победил!", callback_data=f"win_{i}")]
        for i, p in enumerate(players) if not p["out"]
    ]
    rows.append([InlineKeyboardButton(text="🤝  Ничья!", callback_data="draw_result")])
    rows.append([InlineKeyboardButton(text="🔄  Сыграть снова", callback_data="battle", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️  Назад", callback_data="menu", style="primary")],
    ])

def kb_rematch() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄  Реванш!", callback_data="battle", style="danger")],
        [InlineKeyboardButton(text="🏠  Меню",    callback_data="menu")],
    ])

def kb_lobby_creator(players_count: int) -> InlineKeyboardMarkup:
    buttons = []
    if players_count >= 2:
        buttons.append([InlineKeyboardButton(text="🚀 Начать сейчас!", callback_data="start_online", style="success")])
    buttons.append([InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_lobby", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Тренировочные клавиатуры
def kb_solo_draw() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🃏  Тянуть карту!", callback_data="solo_draw")],
        [InlineKeyboardButton(text="🏁  Закончить тренировку", callback_data="solo_finish", style="danger")],
        [InlineKeyboardButton(text="🏳  Сдаться", callback_data="solo_quit", style="primary")],
    ])

def kb_solo_done() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅  Сделано!", callback_data="solo_done", style="success")],
        [InlineKeyboardButton(text="🏳  Сдаться",  callback_data="solo_quit", style="primary")],
    ])

# Клавиатура для рейтинга
def kb_rating() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Моя статистика", callback_data="my_stats", style="primary")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu", style="primary")],
    ])
