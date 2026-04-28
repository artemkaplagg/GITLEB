

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
# FSM СОСТОЯНИЯ
# ──────────────────────────────────────────────
class Game(StatesGroup):
    naming  = State()   # ввод имён игроков
    playing = State()   # игра идёт

# ──────────────────────────────────────────────
# КЛАВИАТУРЫ
# ──────────────────────────────────────────────
def kb_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️  Сразиться!",  callback_data="battle")],
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
# МЕНЮ
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
# НАСТРОЙКА НОВОЙ ИГРЫ
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
        # Все игроки введены — стартуем
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
# ИГРОВОЙ ПРОЦЕСС
# ──────────────────────────────────────────────
async def push_turn(chat_id: int, players: list, idx: int, rnd: int):
    """Отправляет сообщение с ходом текущего игрока."""
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

@dp.callback_query(F.data == "draw", Game.playing)
async def draw_card(cb: CallbackQuery, state: FSMContext):
    data    = await state.get_data()
    players = data["players"]
    idx     = data["cur"]

    suit  = random.choice(SUITS)
    rank  = random.choice(RANKS)
    count = VALUES[rank]

    players[idx]["total"] += count
    players[idx]["rds"]   += 1
    await state.update_data(players=players, last={"suit": suit, "rank": rank, "count": count})

    # Спецэффект для туза и фигурных карт
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

@dp.callback_query(F.data == "done", Game.playing)
async def mark_done(cb: CallbackQuery, state: FSMContext):
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

    # Если начался новый раунд — показать итоги раунда
    if new_rnd > rnd:
        await cb.message.answer(
            f"🏁 *Раунд {rnd} завершён!*\n\n"
            f"{make_scoreboard(players)}\n\n"
            f"🔥 *Раунд {new_rnd} — начали!*",
            parse_mode="Markdown",
        )
        await asyncio.sleep(1)

    await push_turn(cb.message.chat.id, players, nxt, new_rnd)

@dp.callback_query(F.data == "score", Game.playing)
async def show_score(cb: CallbackQuery, state: FSMContext):
    data    = await state.get_data()
    players = data["players"]
    rnd     = data["rnd"]
    await cb.answer()
    await cb.message.answer(
        f"*Раунд {rnd}*\n\n{make_scoreboard(players)}",
        parse_mode="Markdown",
    )

@dp.callback_query(F.data == "quit", Game.playing)
async def player_quit(cb: CallbackQuery, state: FSMContext):
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

@dp.callback_query(F.data == "finish", Game.playing)
async def finish_game(cb: CallbackQuery, state: FSMContext):
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
# ФИНАЛ ИГРЫ
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