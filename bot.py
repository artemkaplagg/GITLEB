import asyncio
import random

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# ──────────────────────────────────────────────
# КОНФИГ
# ──────────────────────────────────────────────
BOT_TOKEN = "8703552780:AAEAe0eQjb3iESuD-KBKBFtuF0q2QafBZCE"
ADMIN_ID = 6185367393
ONLINE_TIMEOUT = 30  # секунд ожидания в лобби

# ──────────────────────────────────────────────
# ДАННЫЕ КАРТ
# ──────────────────────────────────────────────
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

# ──────────────────────────────────────────────
# ГЛОБАЛЬНОЕ ОНЛАЙН-ЛОББИ (только одно)
# ──────────────────────────────────────────────
online_lobby = None

# ──────────────────────────────────────────────
# FSM СОСТОЯНИЯ
# ──────────────────────────────────────────────
class Game(StatesGroup):
    naming  = State()   # ввод имён игроков (локально)
    playing = State()   # игра идёт (локально)

class SettingsState(StatesGroup):
    waiting_timeout = State()  # ожидание нового таймера от админа

# ──────────────────────────────────────────────
# КЛАВИАТУРЫ
# ──────────────────────────────────────────────
def kb_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️  Сразиться!",  callback_data="battle")],
        [InlineKeyboardButton(text="🌐  Онлайн",       callback_data="online")],
        [InlineKeyboardButton(text="📖  Правила",      callback_data="rules"),
         InlineKeyboardButton(text="🏆  Рейтинг",     callback_data="rating")],
    ])

def kb_player_count() -> InlineKeyboardMarkup:
    row = [InlineKeyboardButton(text=str(i), callback_data=f"n_{i}") for i in range(2, 7)]
    return InlineKeyboardMarkup(inline_keyboard=[
        row,
        [InlineKeyboardButton(text="❌ Отмена", callback_data="menu")],
    ])

def kb_draw() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🃏  Тянуть карту!", callback_data="draw")],
        [InlineKeyboardButton(text="📊  Счёт",          callback_data="score"),
         InlineKeyboardButton(text="🏁  Завершить",     callback_data="finish")],
        [InlineKeyboardButton(text="🏳  Сдаться",       callback_data="quit")],
    ])

def kb_done() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅  Сделано!",  callback_data="done")],
        [InlineKeyboardButton(text="🏳  Сдаться",   callback_data="quit")],
    ])

def kb_end(players: list) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"🏆  {p['name']} победил!", callback_data=f"win_{i}")]
        for i, p in enumerate(players) if not p["out"]
    ]
    rows.append([InlineKeyboardButton(text="🤝  Ничья!", callback_data="draw_result")])
    rows.append([InlineKeyboardButton(text="🔄  Сыграть снова", callback_data="battle")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️  Назад", callback_data="menu")],
    ])

def kb_rematch() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄  Реванш!",  callback_data="battle")],
        [InlineKeyboardButton(text="🏠  Меню",     callback_data="menu")],
    ])

def kb_lobby_creator(players_count: int) -> InlineKeyboardMarkup:
    """Клавиатура для создателя лобби."""
    buttons = []
    if players_count >= 2:
        buttons.append([InlineKeyboardButton(text="🚀 Начать сейчас!", callback_data="start_online")])
    buttons.append([InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_lobby")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ──────────────────────────────────────────────
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ──────────────────────────────────────────────
def make_scoreboard(players: list) -> str:
    ranked = sorted(players, key=lambda p: p["total"], reverse=True)
    lines = ["📊 *СЧЁТ:*"]
    for i, p in enumerate(ranked):
        flag = " 🏳" if p["out"] else ""
        lines.append(f"{MEDALS[i]} *{p['name']}* — {p['total']} отж.{flag}")
    return "\n".join(lines)

def active_count(players: list) -> int:
    return sum(1 for p in players if not p["out"])

def next_player(players: list, cur: int, rnd: int) -> tuple[int, int]:
    """Возвращает (следующий индекс, номер раунда)."""
    n = len(players)
    nxt = (cur + 1) % n
    new_rnd = rnd + 1 if nxt <= cur else rnd
    attempts = 0
    while players[nxt]["out"] and attempts < n:
        if nxt == n - 1:
            new_rnd += 1
        nxt = (nxt + 1) % n
        attempts += 1
    return nxt, new_rnd

def card_art(suit: dict, rank: str, count: int) -> str:
    """Красивое ASCII-отображение карты."""
    rank_str  = RANK_DISPLAY[rank]
    suit_line = f"{suit['sym']} {rank_str}"
    return (
        f"┌─────────────────┐\n"
        f"│  {suit_line:<15} │\n"
        f"│                 │\n"
        f"│   {suit['emoji']}  ×{count:<8}  │\n"
        f"│                 │\n"
        f"└─────────────────┘"
    )

def is_online_player(chat_id: int) -> bool:
    """Проверяет, участвует ли пользователь в активной онлайн-игре."""
    global online_lobby
    if not online_lobby or not online_lobby.get("started"):
        return False
    return any(p["chat_id"] == chat_id for p in online_lobby["players"])

# ──────────────────────────────────────────────
# БОТ И ДИСПЕТЧЕР
# ──────────────────────────────────────────────
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())

# ──────────────────────────────────────────────
# /start  /help
# ──────────────────────────────────────────────
@dp.message(Command("start", "help"))
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "💪 *КАРТОЧНЫЙ ДОМИК*\n\n"
        "🎴 Игра в отжимания по картам!\n"
        "Тяни карту — получай задание.\n"
        "Масть = *вид*, номинал = *количество*.\n\n"
        "Выживет сильнейший! 🔥",
        parse_mode="Markdown",
        reply_markup=kb_main(),
    )

# ──────────────────────────────────────────────
# НАСТРОЙКИ (только админ)
# ──────────────────────────────────────────────
@dp.message(Command("settings"))
async def cmd_settings(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ Эта команда только для создателя бота.")
        return

    global ONLINE_TIMEOUT
    await state.set_state(SettingsState.waiting_timeout)
    await msg.answer(
        f"⚙️ *Настройки онлайн-лобби*\n\n"
        f"Текущий таймер ожидания: *{ONLINE_TIMEOUT} сек.*\n"
        f"Введите новое значение (целое число секунд):",
        parse_mode="Markdown",
    )

@dp.message(SettingsState.waiting_timeout)
async def set_timeout(msg: Message, state: FSMContext):
    global ONLINE_TIMEOUT
    try:
        new_val = int(msg.text.strip())
        if new_val < 5 or new_val > 300:
            raise ValueError
        ONLINE_TIMEOUT = new_val
        await msg.answer(f"✅ Таймер обновлён: *{ONLINE_TIMEOUT} сек.*", parse_mode="Markdown")
        await state.clear()
    except:
        await msg.answer("❌ Введи целое число от 5 до 300.")

# ──────────────────────────────────────────────
# МЕНЮ (без изменений, только появилась кнопка Онлайн)
# ──────────────────────────────────────────────
@dp.callback_query(F.data == "menu")
async def go_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(
        "💪 *КАРТОЧНЫЙ ДОМИК*\n\n"
        "🎴 Игра в отжимания по картам!\n"
        "Выживет сильнейший! 🔥",
        parse_mode="Markdown",
        reply_markup=kb_main(),
    )
    await cb.answer()

@dp.callback_query(F.data == "rules")
async def show_rules(cb: CallbackQuery):
    await cb.message.edit_text(
        "📖 *ПРАВИЛА КАРТОЧНОГО ДОМИКА*\n\n"
        "🃏 *Масть = Вид отжиманий:*\n"
        "♥️ 💪 Классические\n"
        "♠️ 🦅 Широкий хват\n"
        "♦️ 💎 Алмазные (руки ромбом)\n"
        "♣️ 💥 Взрывные (с хлопком)\n\n"
        "🔢 *Номинал = Количество:*\n"
        "2–10 → столько же раз\n"
        "Валет / Дама / Король → 12 раз\n"
        "⚡ Туз → 15 раз\n\n"
        "💡 Кто сдался — тот проиграл!\n"
        "🏆 Последний стоящий — чемпион!",
        parse_mode="Markdown",
        reply_markup=kb_back(),
    )
    await cb.answer()

@dp.callback_query(F.data == "rating")
async def show_rating(cb: CallbackQuery):
    await cb.message.edit_text(
        "🏆 *РЕЙТИНГ*\n\n"
        "🚧 *В разработке!*\n\n"
        "Скоро появится:\n"
        "• 🌍 Глобальный рейтинг игроков\n"
        "• 📈 История всех сыгранных игр\n"
        "• 🏅 Рекорды по отжиманиям\n"
        "• 🔥 Серии побед без поражений\n"
        "• 🎖 Ачивки и звания\n\n"
        "*Следи за обновлениями!* 👀",
        parse_mode="Markdown",
        reply_markup=kb_back(),
    )
    await cb.answer()

# ──────────────────────────────────────────────
# НАСТРОЙКА НОВОЙ ИГРЫ (ЛОКАЛЬНО)
# ──────────────────────────────────────────────
@dp.callback_query(F.data == "battle")
async def start_battle(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(
        "⚔️ *НОВАЯ БИТВА!*\n\n"
        "👥 Сколько игроков будет сражаться?\n"
        "*(от 2 до 6)*",
        parse_mode="Markdown",
        reply_markup=kb_player_count(),
    )
    await cb.answer()

@dp.callback_query(F.data.startswith("n_"))
async def set_count(cb: CallbackQuery, state: FSMContext):
    n = int(cb.data[2:])
    await state.set_state(Game.naming)
    await state.update_data(n=n, players=[], rnd=1, cur=0)
    await cb.message.edit_text(
        f"👤 *Игрок 1 из {n}*\n\nВведи своё имя:",
        parse_mode="Markdown",
    )
    await cb.answer()

@dp.message(Game.naming)
async def collect_names(msg: Message, state: FSMContext):
    data    = await state.get_data()
    players = data["players"]
    n       = data["n"]

    name = msg.text.strip()[:20]
    players.append({"name": name, "total": 0, "rds": 0, "out": False})
    await state.update_data(players=players)

    if len(players) < n:
        await msg.answer(
            f"✅ *{name}* — в игре!\n\n"
            f"👤 *Игрок {len(players) + 1} из {n}*\n\nВведи имя:",
            parse_mode="Markdown",
        )
    else:
        await state.set_state(Game.playing)
        names_line = " ⚔️ ".join(f"*{p['name']}*" for p in players)
        await msg.answer(
            f"🔥 *БИТВА НАЧИНАЕТСЯ!*\n\n"
            f"{names_line}\n\n"
            f"🎴 Карты перемешаны...\n"
            f"Пусть победит сильнейший! 💪",
            parse_mode="Markdown",
        )
        await asyncio.sleep(1)
        await push_turn(msg.chat.id, players, 0, 1)

# ──────────────────────────────────────────────
# ОНЛАЙН-ЛОББИ
# ──────────────────────────────────────────────
async def update_lobby_message():
    """Обновляет сообщение создателя с информацией о лобби."""
    global online_lobby
    if not online_lobby or online_lobby["started"]:
        return

    names = "\n".join(f"• {p['name']}" for p in online_lobby["players"])
    text = (
        f"🌐 *ОНЛАЙН-ЛОББИ*\n\n"
        f"Игроки ({len(online_lobby['players'])}):\n{names}\n\n"
        f"Ожидание {ONLINE_TIMEOUT} сек...\n"
        f"Отправь ссылку друзьям, чтобы они нажали /start и кнопку «🌐 Онлайн»!"
    )
    try:
        await bot.edit_message_text(
            chat_id=online_lobby["creator"],
            message_id=online_lobby["message_id"],
            text=text,
            parse_mode="Markdown",
            reply_markup=kb_lobby_creator(len(online_lobby["players"])),
        )
    except:
        pass

async def timeout_lobby():
    """Вызывается по истечении таймера: запускает игру или отменяет."""
    global online_lobby
    if not online_lobby or online_lobby["started"]:
        return

    if len(online_lobby["players"]) >= 2:
        await start_online_game()
    else:
        await bot.send_message(
            online_lobby["creator"],
            "⌛ Время вышло, а игроков меньше двух. Лобби отменено."
        )
        online_lobby = None

@dp.callback_query(F.data == "online")
async def join_online(cb: CallbackQuery, state: FSMContext):
    global online_lobby
    user_id = cb.from_user.id
    user_name = cb.from_user.full_name

    # Если уже есть активная начатая игра, в которой участвует пользователь – отклоняем
    if online_lobby and online_lobby["started"]:
        if is_online_player(user_id):
            await cb.answer("Ты уже в игре!")
            return
        else:
            await cb.answer("Сейчас идёт онлайн-игра. Дождись завершения.")
            return

    # Если лобби не существует – создаём новое
    if not online_lobby:
        online_lobby = {
            "creator": user_id,
            "players": [{"chat_id": user_id, "name": user_name, "total": 0, "rds": 0, "out": False}],
            "started": False,
            "message_id": None,
            "timer_task": None,
            "cur": 0,
            "rnd": 1,
        }
        # Отправляем сообщение создателю
        msg = await bot.send_message(
            user_id,
            "🌐 *ОНЛАЙН-ЛОББИ*\n\n"
            "Ожидание игроков...",
            parse_mode="Markdown",
            reply_markup=kb_lobby_creator(1),
        )
        online_lobby["message_id"] = msg.message_id
        online_lobby["timer_task"] = asyncio.create_task(asyncio.sleep(ONLINE_TIMEOUT))
        # Запускаем ожидание таймера
        asyncio.create_task(timer_wrapper())
        await cb.answer("Лобби создано! Жди друзей.")
        return

    # Лобби существует (не начатое) – присоединяем игрока
    if any(p["chat_id"] == user_id for p in online_lobby["players"]):
        await cb.answer("Ты уже в лобби!")
        return

    if len(online_lobby["players"]) >= 6:
        await cb.answer("Лобби заполнено (максимум 6).")
        return

    online_lobby["players"].append({
        "chat_id": user_id,
        "name": user_name,
        "total": 0,
        "rds": 0,
        "out": False,
    })
    await update_lobby_message()

    await bot.send_message(user_id, f"✅ Ты в лобби! Игроков: {len(online_lobby['players'])}")
    await cb.answer("Ты присоединился!")
    # Уведомим создателя (но он и так видит обновление)

async def timer_wrapper():
    """Ждёт таймер и вызывает timeout_lobby."""
    global online_lobby
    if not online_lobby or online_lobby["started"]:
        return
    try:
        await online_lobby["timer_task"]
        await timeout_lobby()
    except asyncio.CancelledError:
        pass

@dp.callback_query(F.data == "start_online")
async def start_online_manually(cb: CallbackQuery):
    global online_lobby
    if not online_lobby or online_lobby["started"]:
        await cb.answer("Лобби уже неактивно.")
        return
    if cb.from_user.id != online_lobby["creator"]:
        await cb.answer("Только создатель может начать игру.")
        return
    if len(online_lobby["players"]) < 2:
        await cb.answer("Недостаточно игроков.")
        return

    if online_lobby["timer_task"]:
        online_lobby["timer_task"].cancel()
    await start_online_game()
    await cb.answer()

@dp.callback_query(F.data == "cancel_lobby")
async def cancel_lobby(cb: CallbackQuery):
    global online_lobby
    if not online_lobby or online_lobby["started"]:
        await cb.answer("Лобби уже неактивно.")
        return
    if cb.from_user.id != online_lobby["creator"]:
        await cb.answer("Только создатель может отменить.")
        return

    if online_lobby["timer_task"]:
        online_lobby["timer_task"].cancel()
    await bot.send_message(online_lobby["creator"], "❌ Лобби отменено.")
    online_lobby = None
    await cb.answer("Лобби отменено.")
    await cb.message.edit_text("Лобби отменено.")

# ──────────────────────────────────────────────
# ЗАПУСК ОНЛАЙН-ИГРЫ
# ──────────────────────────────────────────────
async def start_online_game():
    global online_lobby
    if not online_lobby:
        return
    online_lobby["started"] = True
    players = online_lobby["players"]
    online_lobby["cur"] = 0
    online_lobby["rnd"] = 1

    names_line = " ⚔️ ".join(f"*{p['name']}*" for p in players)
    for p in players:
        await bot.send_message(
            p["chat_id"],
            f"🔥 *ОНЛАЙН-БИТВА НАЧИНАЕТСЯ!*\n\n{names_line}\n\n"
            f"Первый ход: *{players[0]['name']}*",
            parse_mode="Markdown",
        )

    # Ход первого игрока
    await push_online_turn(0)

async def push_online_turn(idx: int):
    """Отправляет ход текущему игроку в онлайне."""
    global online_lobby
    players = online_lobby["players"]
    p = players[idx]
    alive = active_count(players)
    # Сообщение только текущему игроку с кнопками
    await bot.send_message(
        p["chat_id"],
        f"🎮 *Раунд {online_lobby['rnd']}*  |  Игроков: {alive}\n"
        f"{'─' * 24}\n"
        f"🎯 Твой ход, *{p['name']}*!.",
        parse_mode="Markdown",
        reply_markup=kb_draw(),
    )
    # Оповещаем остальных
    for other in players:
        if other["chat_id"] != p["chat_id"] and not other["out"]:
            await bot.send_message(
                other["chat_id"],
                f"⏳ Ход *{p['name']}*...",
                parse_mode="Markdown",
            )

# ──────────────────────────────────────────────
# ИГРОВОЙ ПРОЦЕСС (ЛОКАЛЬНЫЙ) – дополнен проверкой онлайна
# ──────────────────────────────────────────────
async def push_turn(chat_id: int, players: list, idx: int, rnd: int):
    """Отправляет сообщение с ходом текущего игрока (локально)."""
    p     = players[idx]
    alive = active_count(players)
    await bot.send_message(
        chat_id,
        f"🎮 *Раунд {rnd}*  |  Игроков: {alive}\n"
        f"{'─' * 24}\n"
        f"🎯 Ход: *{p['name']}*\n\n"
        f"Готов? Тяни карту! 👇",
        parse_mode="Markdown",
        reply_markup=kb_draw(),
    )

@dp.callback_query(F.data == "draw")
async def draw_card(cb: CallbackQuery, state: FSMContext):
    # Если пользователь в онлайн-игре – своя логика
    if is_online_player(cb.from_user.id):
        await online_draw(cb)
        return

    # Локальная игра через FSM
    data    = await state.get_data()
    players = data["players"]
    idx     = data["cur"]

    suit  = random.choice(SUITS)
    rank  = random.choice(RANKS)
    count = VALUES[rank]

    players[idx]["total"] += count
    players[idx]["rds"]   += 1
    await state.update_data(players=players, last={"suit": suit, "rank": rank, "count": count})

    special = ""
    if rank == "A":
        special = "\n\n⚡ *ТУЗА ВЫТЯНУЛ!* Это сразу 15 раз — держись! 😤"
    elif rank in ("J", "Q", "K"):
        special = "\n\n👑 *Фигурная карта* — 12 раз, не меньше!"

    await cb.message.edit_text(
        f"🃏 *{players[idx]['name']} тянет карту...*\n\n"
        f"`{card_art(suit, rank, count)}`\n"
        f"{special}\n\n"
        f"_{suit['tip']}_\n\n"
        f"Давай, *{players[idx]['name']}*! 💪",
        parse_mode="Markdown",
        reply_markup=kb_done(),
    )
    await cb.answer("🃏 Карта вытянута!")

@dp.callback_query(F.data == "done")
async def mark_done(cb: CallbackQuery, state: FSMContext):
    if is_online_player(cb.from_user.id):
        await online_done(cb)
        return

    data    = await state.get_data()
    players = data["players"]
    idx     = data["cur"]
    rnd     = data["rnd"]
    last    = data.get("last", {})
    count   = last.get("count", 0)
    name    = players[idx]["name"]

    await cb.message.edit_text(
        f"✅ *{name}* выполнил *{count}* отж.! Красавчик! 💪\n"
        f"📊 Всего у *{name}*: *{players[idx]['total']}*",
        parse_mode="Markdown",
    )
    await cb.answer("✅ Засчитано!")

    nxt, new_rnd = next_player(players, idx, rnd)
    await state.update_data(cur=nxt, rnd=new_rnd)

    await asyncio.sleep(1.5)

    if new_rnd > rnd:
        await cb.message.answer(
            f"🏁 *Раунд {rnd} завершён!*\n\n"
            f"{make_scoreboard(players)}\n\n"
            f"🔥 *Раунд {new_rnd} — начали!*",
            parse_mode="Markdown",
        )
        await asyncio.sleep(1)

    await push_turn(cb.message.chat.id, players, nxt, new_rnd)

@dp.callback_query(F.data == "score")
async def show_score(cb: CallbackQuery, state: FSMContext):
    if is_online_player(cb.from_user.id):
        await online_score(cb)
        return

    data    = await state.get_data()
    players = data["players"]
    rnd     = data["rnd"]
    await cb.answer()
    await cb.message.answer(
        f"*Раунд {rnd}*\n\n{make_scoreboard(players)}",
        parse_mode="Markdown",
    )

@dp.callback_query(F.data == "quit")
async def player_quit(cb: CallbackQuery, state: FSMContext):
    if is_online_player(cb.from_user.id):
        await online_quit(cb)
        return

    data    = await state.get_data()
    players = data["players"]
    idx     = data["cur"]
    rnd     = data["rnd"]

    name               = players[idx]["name"]
    players[idx]["out"] = True
    await state.update_data(players=players)

    alive = [p for p in players if not p["out"]]

    if len(alive) == 1:
        w = alive[0]
        await cb.message.edit_text(
            f"🏳 *{name}* не выдержал и сдался!\n\n"
            f"🏆 *{w['name'].upper()} — ПОБЕДИТЕЛЬ!* 🏆\n\n"
            f"{make_scoreboard(players)}",
            parse_mode="Markdown",
            reply_markup=kb_rematch(),
        )
        await state.clear()

    elif len(alive) == 0:
        await cb.message.edit_text(
            f"🏳 Все сдались! 😅\n\n{make_scoreboard(players)}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Сыграть снова", callback_data="battle")],
            ]),
        )
        await state.clear()

    else:
        await cb.message.edit_text(
            f"🏳 *{name}* сдался...\n"
            f"Осталось в строю: *{len(alive)}* 💪",
            parse_mode="Markdown",
        )
        nxt, new_rnd = next_player(players, idx, rnd)
        await state.update_data(cur=nxt, rnd=new_rnd)
        await asyncio.sleep(1.5)
        await push_turn(cb.message.chat.id, players, nxt, new_rnd)

    await cb.answer()

@dp.callback_query(F.data == "finish")
async def finish_game(cb: CallbackQuery, state: FSMContext):
    if is_online_player(cb.from_user.id):
        await online_finish(cb)
        return

    data    = await state.get_data()
    players = data["players"]
    rnd     = data["rnd"]
    await cb.message.edit_text(
        f"🏁 *ИГРА ЗАВЕРШЕНА!*  *(Раунд {rnd})*\n\n"
        f"{make_scoreboard(players)}\n\n"
        f"Кто победил?",
        parse_mode="Markdown",
        reply_markup=kb_end(players),
    )
    await cb.answer()

# ──────────────────────────────────────────────
# ОНЛАЙН ИГРОВЫЕ ДЕЙСТВИЯ
# ──────────────────────────────────────────────
async def online_draw(cb: CallbackQuery):
    global online_lobby
    players = online_lobby["players"]
    cur = online_lobby["cur"]
    if cb.from_user.id != players[cur]["chat_id"]:
        await cb.answer("Сейчас не твой ход!")
        return

    suit  = random.choice(SUITS)
    rank  = random.choice(RANKS)
    count = VALUES[rank]

    players[cur]["total"] += count
    players[cur]["rds"]   += 1
    online_lobby["last"] = {"suit": suit, "rank": rank, "count": count}

    special = ""
    if rank == "A":
        special = "\n\n⚡ *ТУЗА ВЫТЯНУЛ!* Это сразу 15 раз — держись! 😤"
    elif rank in ("J", "Q", "K"):
        special = "\n\n👑 *Фигурная карта* — 12 раз, не меньше!"

    # Показываем карту только текущему
    await cb.message.edit_text(
        f"🃏 *Ты вытянул карту!*\n\n"
        f"`{card_art(suit, rank, count)}`\n"
        f"{special}\n\n"
        f"_{suit['tip']}_\n\n"
        f"Сделай *{count}* отжиманий! 💪",
        parse_mode="Markdown",
        reply_markup=kb_done(),
    )
    # Оповещаем остальных
    for p in players:
        if p["chat_id"] != cb.from_user.id and not p["out"]:
            await bot.send_message(
                p["chat_id"],
                f"🃏 *{players[cur]['name']}* тянет карту... *{rank} {suit['sym']}* — {count} отж.",
                parse_mode="Markdown",
            )
    await cb.answer("Карта вытянута!")

async def online_done(cb: CallbackQuery):
    global online_lobby
    players = online_lobby["players"]
    cur = online_lobby["cur"]
    if cb.from_user.id != players[cur]["chat_id"]:
        await cb.answer("Не твой ход!")
        return

    last = online_lobby.get("last", {})
    count = last.get("count", 0)
    name = players[cur]["name"]

    await cb.message.edit_text(
        f"✅ Ты сделал *{count}* отж.! Всего у тебя *{players[cur]['total']}*.",
        parse_mode="Markdown",
    )
    await cb.answer("Засчитано!")

    # Переход хода
    rnd = online_lobby["rnd"]
    nxt, new_rnd = next_player(players, cur, rnd)
    online_lobby["cur"] = nxt
    online_lobby["rnd"] = new_rnd

    if new_rnd > rnd:
        # итоги раунда всем
        for p in players:
            if not p["out"]:
                await bot.send_message(
                    p["chat_id"],
                    f"🏁 *Раунд {rnd} завершён!*\n\n{make_scoreboard(players)}",
                    parse_mode="Markdown",
                )

    await push_online_turn(nxt)

async def online_score(cb: CallbackQuery):
    global online_lobby
    players = online_lobby["players"]
    await cb.answer()
    await cb.message.answer(
        f"📊 *Раунд {online_lobby['rnd']}*\n\n{make_scoreboard(players)}",
        parse_mode="Markdown",
    )

async def online_quit(cb: CallbackQuery):
    global online_lobby
    players = online_lobby["players"]
    cur = online_lobby["cur"]
    user_id = cb.from_user.id

    # Найти игрока
    idx = None
    for i, p in enumerate(players):
        if p["chat_id"] == user_id:
            idx = i
            break
    if idx is None:
        await cb.answer("Ты не в игре.")
        return

    name = players[idx]["name"]
    players[idx]["out"] = True

    alive = [p for p in players if not p["out"]]

    # Оповещаем всех
    if len(alive) == 1:
        winner = alive[0]
        for p in players:
            await bot.send_message(
                p["chat_id"],
                f"🏳 *{name}* сдался!\n\n"
                f"🏆 *{winner['name'].upper()} — ПОБЕДИТЕЛЬ!* 🏆\n\n{make_scoreboard(players)}",
                parse_mode="Markdown",
            )
        online_lobby = None
    elif len(alive) == 0:
        for p in players:
            await bot.send_message(p["chat_id"], "Все сдались! 😅")
        online_lobby = None
    else:
        for p in players:
            await bot.send_message(
                p["chat_id"],
                f"🏳 *{name}* сдался. Осталось в строю: *{len(alive)}*",
                parse_mode="Markdown",
            )
        # Если сдался текущий игрок, переходим к следующему
        if idx == online_lobby["cur"]:
            rnd = online_lobby["rnd"]
            nxt, new_rnd = next_player(players, idx, rnd)
            online_lobby["cur"] = nxt
            online_lobby["rnd"] = new_rnd
            await push_online_turn(nxt)

    await cb.answer()

async def online_finish(cb: CallbackQuery):
    global online_lobby
    players = online_lobby["players"]
    rnd = online_lobby["rnd"]

    # Определяем победителя по очкам
    alive = [p for p in players if not p["out"]]
    if alive:
        winner = max(alive, key=lambda x: x["total"])
        for p in players:
            await bot.send_message(
                p["chat_id"],
                f"🏁 *ИГРА ЗАВЕРШЕНА!* (Раунд {rnd})\n\n{make_scoreboard(players)}\n\n"
                f"🏆 *{winner['name'].upper()} — ЧЕМПИОН!*",
                parse_mode="Markdown",
            )
    else:
        for p in players:
            await bot.send_message(p["chat_id"], "Игра завершена, ни одного финишёра.")

    online_lobby = None
    await cb.answer("Игра завершена!")

# ──────────────────────────────────────────────
# ФИНАЛ ЛОКАЛЬНОЙ ИГРЫ (без изменений)
# ──────────────────────────────────────────────
@dp.callback_query(F.data.startswith("win_"))
async def declare_winner(cb: CallbackQuery, state: FSMContext):
    data    = await state.get_data()
    players = data.get("players", [])
    i       = int(cb.data[4:])

    if i >= len(players):
        await cb.answer("Ошибка!")
        return

    w = players[i]
    await cb.message.edit_text(
        f"🏆 *{w['name'].upper()} — ЧЕМПИОН!* 🏆\n\n"
        f"💪 Отжиманий сделано: *{w['total']}*\n"
        f"🔄 Раундов пережито: *{w['rds']}*\n\n"
        f"{make_scoreboard(players)}\n\n"
        f"_Тренируйся каждый день!_ 🔥",
        parse_mode="Markdown",
        reply_markup=kb_rematch(),
    )
    await state.clear()
    await cb.answer(f"🏆 {w['name']} побеждает!")

@dp.callback_query(F.data == "draw_result")
async def declare_draw(cb: CallbackQuery, state: FSMContext):
    data    = await state.get_data()
    players = data.get("players", [])
    await cb.message.edit_text(
        f"🤝 *НИЧЬЯ!*\n\n"
        f"Все бойцы показали силу духа!\n\n"
        f"{make_scoreboard(players)}\n\n"
        f"*В следующий раз выясним сильнейшего!* 💪",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Сыграть снова!", callback_data="battle")],
        ]),
    )
    await state.clear()
    await cb.answer()

# ──────────────────────────────────────────────
# ОБРАБОТКА НЕИЗВЕСТНЫХ СООБЩЕНИЙ
# ──────────────────────────────────────────────
@dp.message()
async def fallback(msg: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await msg.answer(
            "Привет! 👋 Нажми /start чтобы начать игру.",
            reply_markup=kb_main(),
        )

# ──────────────────────────────────────────────
# ЗАПУСК
# ──────────────────────────────────────────────
async def main():
    print("🃏 КАРТОЧНЫЙ ДОМИК запущен!")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    asyncio.run(main())