# handlers.py (ПОЛНЫЙ, включая онлайн)
import asyncio, random
from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
import config
from config import Game, SettingsState, TrainingState, SUITS, RANKS, VALUES, RANK_DISPLAY, MEDALS, WIN_REACTIONS
from keyboards import *
from rating import update_player_stats, get_top, get_user_stats, ACHIEVEMENTS
from main import bot, dp

# ============== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==============
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
    if not config.online_lobby or not config.online_lobby.get("started"):
        return False
    return any(p["chat_id"] == chat_id for p in config.online_lobby["players"])

# ============== ОБЩИЕ ХЕНДЛЕРЫ ==============
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

@dp.message(Command("settings"))
async def cmd_settings(msg: Message, state: FSMContext):
    if msg.from_user.id != config.ADMIN_ID:
        await msg.answer("⛔ Эта команда только для создателя бота.")
        return
    await state.set_state(SettingsState.waiting_timeout)
    await msg.answer(
        f"⚙️ *Настройки онлайн-лобби*\n\n"
        f"Текущий таймер ожидания: *{config.ONLINE_TIMEOUT} сек.*\n"
        f"Введите новое значение (целое число секунд):",
        parse_mode="Markdown",
    )

@dp.message(SettingsState.waiting_timeout)
async def set_timeout(msg: Message, state: FSMContext):
    try:
        new_val = int(msg.text.strip())
        if new_val < 5 or new_val > 300:
            raise ValueError
        config.ONLINE_TIMEOUT = new_val
        await msg.answer(f"✅ Таймер обновлён: *{config.ONLINE_TIMEOUT} сек.*", parse_mode="Markdown")
        await state.clear()
    except:
        await msg.answer("❌ Введи целое число от 5 до 300.")

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
    top = get_top(10)
    if top:
        lines = ["🏆 *ТОП-10 РЕЙТИНГА*\n"]
        for i, (uid, name, score, wins, games, pushups) in enumerate(top, 1):
            lines.append(f"{i}. {name} — {score} очк. ({wins} побед, {pushups} отж.)")
        text = "\n".join(lines)
    else:
        text = "Рейтинг пока пуст."
    await cb.message.edit_text(text, parse_mode="Markdown", reply_markup=kb_rating())
    await cb.answer()

@dp.callback_query(F.data == "my_stats")
async def show_my_stats(cb: CallbackQuery):
    stats = get_user_stats(cb.from_user.id)
    if not stats:
        await cb.message.edit_text("Ты пока не сыграл ни одной игры.", reply_markup=kb_back())
        return
    ach_list = "\n".join(ACHIEVEMENTS[a]["name"] for a in stats.get("achievements", [])) or "нет"
    text = (
        f"📊 *{stats['name']}*\n"
        f"━━━━━━━━━━━━━\n"
        f"🎮 Игр: {stats['games']}\n"
        f"🏆 Побед: {stats['wins']}\n"
        f"😞 Поражений: {stats['losses']}\n"
        f"💪 Всего отжиманий: {stats['total_pushups']}\n"
        f"🔥 Рекорд за игру: {stats['max_pushups_one_game']}\n"
        f"🏋️ Тренировок: {stats['trainings']}\n"
        f"🎖 Достижения:\n{ach_list}"
    )
    await cb.message.edit_text(text, parse_mode="Markdown", reply_markup=kb_back())
    await cb.answer()

# ============== ЛОКАЛЬНАЯ ИГРА ==============
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
    await cb.message.edit_text(f"👤 *Игрок 1 из {n}*\n\nВведи своё имя:", parse_mode="Markdown")
    await cb.answer()

@dp.message(Game.naming)
async def collect_names(msg: Message, state: FSMContext):
    data = await state.get_data()
    players = data["players"]
    n = data["n"]
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
            f"🔥 *БИТВА НАЧИНАЕТСЯ!*\n\n{names_line}\n\n"
            f"🎴 Карты перемешаны...\nПусть победит сильнейший! 💪",
            parse_mode="Markdown",
        )
        await asyncio.sleep(1)
        await push_turn(msg.chat.id, players, 0, 1)

async def push_turn(chat_id: int, players: list, idx: int, rnd: int):
    p = players[idx]
    alive = active_count(players)
    await bot.send_message(
        chat_id,
        f"🎮 *Раунд {rnd}*  |  Игроков: {alive}\n{'─'*24}\n"
        f"🎯 Ход: *{p['name']}*\n\nГотов? Тяни карту! 👇",
        parse_mode="Markdown", reply_markup=kb_draw(),
    )

@dp.callback_query(F.data == "draw")
async def draw_card(cb: CallbackQuery, state: FSMContext):
    # Онлайн-игроки обрабатываются отдельно
    if is_online_player(cb.from_user.id):
        await online_draw(cb)
        return
    # Локальная игра
    data = await state.get_data()
    players = data["players"]
    idx = data["cur"]
    suit = random.choice(SUITS)
    rank = random.choice(RANKS)
    count = VALUES[rank]
    players[idx]["total"] += count
    players[idx]["rds"] += 1
    await state.update_data(players=players, last={"suit": suit, "rank": rank, "count": count})
    special = ""
    if rank == "A":
        special = "\n\n⚡ *ТУЗА ВЫТЯНУЛ!* Это сразу 15 раз — держись! 😤"
    elif rank in ("J", "Q", "K"):
        special = "\n\n👑 *Фигурная карта* — 12 раз, не меньше!"
    await cb.message.edit_text(
        f"🃏 *{players[idx]['name']} тянет карту...*\n\n"
        f"`{card_art(suit, rank, count)}`\n{special}\n\n"
        f"_{suit['tip']}_\n\nДавай, *{players[idx]['name']}*! 💪",
        parse_mode="Markdown", reply_markup=kb_done(),
    )
    await cb.answer("🃏 Карта вытянута!")

@dp.callback_query(F.data == "done")
async def mark_done(cb: CallbackQuery, state: FSMContext):
    if is_online_player(cb.from_user.id):
        await online_done(cb)
        return
    data = await state.get_data()
    players = data["players"]
    idx = data["cur"]
    rnd = data["rnd"]
    last = data.get("last", {})
    count = last.get("count", 0)
    name = players[idx]["name"]
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
            f"🏁 *Раунд {rnd} завершён!*\n\n{make_scoreboard(players)}\n\n🔥 *Раунд {new_rnd} — начали!*",
            parse_mode="Markdown",
        )
        await asyncio.sleep(1)
    await push_turn(cb.message.chat.id, players, nxt, new_rnd)

@dp.callback_query(F.data == "score")
async def show_score(cb: CallbackQuery, state: FSMContext):
    if is_online_player(cb.from_user.id):
        await online_score(cb)
        return
    data = await state.get_data()
    await cb.answer()
    await cb.message.answer(
        f"*Раунд {data['rnd']}*\n\n{make_scoreboard(data['players'])}",
        parse_mode="Markdown",
    )

@dp.callback_query(F.data == "quit")
async def player_quit(cb: CallbackQuery, state: FSMContext):
    if is_online_player(cb.from_user.id):
        await online_quit(cb)
        return
    data = await state.get_data()
    players = data["players"]
    idx = data["cur"]
    rnd = data["rnd"]
    name = players[idx]["name"]
    players[idx]["out"] = True
    await state.update_data(players=players)
    alive = [p for p in players if not p["out"]]
    if len(alive) == 1:
        w = alive[0]
        for p in players:
            update_player_stats(p.get("chat_id", 0), p["name"], {
                "game_type": "local", "won": not p["out"],
                "total_pushups": p["total"], "rounds": p["rds"]
            })
        await cb.message.edit_text(
            f"🏳 *{name}* не выдержал и сдался!\n\n"
            f"🏆 *{w['name'].upper()} — ПОБЕДИТЕЛЬ!* 🏆\n\n{make_scoreboard(players)}",
            parse_mode="Markdown", reply_markup=kb_rematch(),
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
            f"🏳 *{name}* сдался...\nОсталось в строю: *{len(alive)}* 💪",
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
    data = await state.get_data()
    await cb.message.edit_text(
        f"🏁 *ИГРА ЗАВЕРШЕНА!*  *(Раунд {data['rnd']})*\n\n"
        f"{make_scoreboard(data['players'])}\n\nКто победил?",
        parse_mode="Markdown", reply_markup=kb_end(data['players']),
    )
    await cb.answer()

@dp.callback_query(F.data.startswith("win_"))
async def declare_winner(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    players = data.get("players", [])
    i = int(cb.data[4:])
    if i >= len(players):
        await cb.answer("Ошибка!"); return
    w = players[i]
    for p in players:
        update_player_stats(p.get("chat_id", 0), p["name"], {
            "game_type": "local", "won": not p["out"],
            "total_pushups": p["total"], "rounds": p["rds"]
        })
    react = random.choice(WIN_REACTIONS)
    await cb.message.edit_text(
        f"🏆 *{w['name'].upper()} — ЧЕМПИОН!* {react}\n\n"
        f"💪 Отжиманий сделано: *{w['total']}*\n"
        f"🔄 Раундов пережито: *{w['rds']}*\n\n{make_scoreboard(players)}\n\n"
        f"_Тренируйся каждый день!_ 🔥",
        parse_mode="Markdown", reply_markup=kb_rematch(),
    )
    await state.clear()
    await cb.answer(f"🏆 {w['name']} побеждает!")

@dp.callback_query(F.data == "draw_result")
async def declare_draw(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    players = data.get("players", [])
    await cb.message.edit_text(
        f"🤝 *НИЧЬЯ!*\n\nВсе бойцы показали силу духа!\n\n"
        f"{make_scoreboard(players)}\n\n"
        f"*В следующий раз выясним сильнейшего!* 💪",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Сыграть снова!", callback_data="battle")],
        ]),
    )
    await state.clear()
    await cb.answer()

# ============== ТРЕНИРОВКА ==============
@dp.callback_query(F.data == "solo")
async def start_solo(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(TrainingState.playing)
    await state.update_data(total=0, rounds=0)
    await cb.message.edit_text(
        "🏋️ *ТРЕНИРОВКА*\n\nТяни карту и отжимайся без ограничений.\n"
        "Нажми «Закончить тренировку» когда устанешь.",
        parse_mode="Markdown", reply_markup=kb_solo_draw(),
    )
    await cb.answer()

@dp.callback_query(F.data == "solo_draw", TrainingState.playing)
async def solo_draw(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    total = data.get("total", 0)
    rounds = data.get("rounds", 0)
    suit = random.choice(SUITS)
    rank = random.choice(RANKS)
    count = VALUES[rank]
    total += count
    rounds += 1
    await state.update_data(total=total, rounds=rounds, last_count=count)
    special = ""
    if rank == "A":
        special = "\n\n⚡ *ТУЗА ВЫТЯНУЛ!* 15 раз!"
    elif rank in ("J", "Q", "K"):
        special = "\n\n👑 *Фигурная карта* — 12 раз!"
    await cb.message.edit_text(
        f"🃏 *Тренировочная карта*\n\n`{card_art(suit, rank, count)}`\n{special}\n"
        f"_{suit['tip']}_\n\nСделай *{count}* отж. (всего: {total})",
        parse_mode="Markdown", reply_markup=kb_solo_done(),
    )
    await cb.answer("🃏")

@dp.callback_query(F.data == "solo_done", TrainingState.playing)
async def solo_done(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await cb.message.edit_text(
        f"✅ Сделано! Продолжай тянуть карты.\nВсего сегодня: *{data['total']}* отж.",
        parse_mode="Markdown", reply_markup=kb_solo_draw(),
    )
    await cb.answer()

@dp.callback_query(F.data == "solo_finish", TrainingState.playing)
async def solo_finish(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    total = data.get("total", 0)
    rounds = data.get("rounds", 0)
    new_ach = update_player_stats(cb.from_user.id, cb.from_user.full_name, {
        "game_type": "training", "total_pushups": total, "rounds": rounds
    })
    ach_text = "\n".join(ACHIEVEMENTS[a]["name"] for a in new_ach) if new_ach else ""
    await cb.message.edit_text(
        f"🏁 *Тренировка окончена!*\n\n💪 Сделано: *{total}* отж. за {rounds} карт.\n"
        f"{'🎖 Новые достижения:\n' + ach_text if ach_text else ''}",
        parse_mode="Markdown", reply_markup=kb_back(),
    )
    await state.clear()
    await cb.answer("Отличная работа!")

@dp.callback_query(F.data == "solo_quit", TrainingState.playing)
async def solo_quit(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("Тренировка прервана.", reply_markup=kb_back())
    await cb.answer()

# ============== ОНЛАЙН-ЛОББИ (ПОЛНОСТЬЮ) ==============
async def update_lobby_message():
    if not config.online_lobby or config.online_lobby["started"]:
        return
    names = "\n".join(f"• {p['name']}" for p in config.online_lobby["players"])
    text = (
        f"🌐 *ОНЛАЙН-ЛОББИ*\n\nИгроки ({len(config.online_lobby['players'])}):\n{names}\n\n"
        f"Ожидание {config.ONLINE_TIMEOUT} сек...\n"
        f"Отправь ссылку друзьям, чтобы они нажали /start и кнопку «🌐 Онлайн»!"
    )
    try:
        await bot.edit_message_text(
            chat_id=config.online_lobby["creator"],
            message_id=config.online_lobby["message_id"],
            text=text, parse_mode="Markdown",
            reply_markup=kb_lobby_creator(len(config.online_lobby["players"])),
        )
    except:
        pass

async def timeout_lobby():
    if not config.online_lobby or config.online_lobby["started"]:
        return
    if len(config.online_lobby["players"]) >= 2:
        await start_online_game()
    else:
        await bot.send_message(config.online_lobby["creator"], "⌛ Время вышло, а игроков меньше двух. Лобби отменено.")
        config.online_lobby = None

@dp.callback_query(F.data == "online")
async def join_online(cb: CallbackQuery, state: FSMContext):
    global online_lobby
    user_id = cb.from_user.id
    user_name = cb.from_user.full_name
    if config.online_lobby and config.online_lobby["started"]:
        if is_online_player(user_id):
            await cb.answer("Ты уже в игре!"); return
        else:
            await cb.answer("Сейчас идёт онлайн-игра. Дождись завершения."); return
    if not config.online_lobby:
        config.online_lobby = {
            "creator": user_id,
            "players": [{"chat_id": user_id, "name": user_name, "total": 0, "rds": 0, "out": False}],
            "started": False, "message_id": None, "timer_task": None, "cur": 0, "rnd": 1,
        }
        msg = await bot.send_message(user_id, "🌐 *ОНЛАЙН-ЛОББИ*\n\nОжидание игроков...", parse_mode="Markdown",
                                     reply_markup=kb_lobby_creator(1))
        config.online_lobby["message_id"] = msg.message_id
        config.online_lobby["timer_task"] = asyncio.create_task(asyncio.sleep(config.ONLINE_TIMEOUT))
        asyncio.create_task(timer_wrapper())
        await cb.answer("Лобби создано! Жди друзей."); return
    # присоединение
    if any(p["chat_id"] == user_id for p in config.online_lobby["players"]):
        await cb.answer("Ты уже в лобби!"); return
    if len(config.online_lobby["players"]) >= 6:
        await cb.answer("Лобби заполнено (максимум 6)."); return
    config.online_lobby["players"].append({
        "chat_id": user_id, "name": user_name, "total": 0, "rds": 0, "out": False,
    })
    await update_lobby_message()
    await bot.send_message(user_id, f"✅ Ты в лобби! Игроков: {len(config.online_lobby['players'])}")
    await cb.answer("Ты присоединился!")

async def timer_wrapper():
    if not config.online_lobby or config.online_lobby["started"]:
        return
    try:
        await config.online_lobby["timer_task"]
        await timeout_lobby()
    except asyncio.CancelledError:
        pass

@dp.callback_query(F.data == "start_online")
async def start_online_manually(cb: CallbackQuery):
    if not config.online_lobby or config.online_lobby["started"]:
        await cb.answer("Лобби уже неактивно."); return
    if cb.from_user.id != config.online_lobby["creator"]:
        await cb.answer("Только создатель может начать игру."); return
    if len(config.online_lobby["players"]) < 2:
        await cb.answer("Недостаточно игроков."); return
    if config.online_lobby["timer_task"]:
        config.online_lobby["timer_task"].cancel()
    await start_online_game()
    await cb.answer()

@dp.callback_query(F.data == "cancel_lobby")
async def cancel_lobby(cb: CallbackQuery):
    if not config.online_lobby or config.online_lobby["started"]:
        await cb.answer("Лобби уже неактивно."); return
    if cb.from_user.id != config.online_lobby["creator"]:
        await cb.answer("Только создатель может отменить."); return
    if config.online_lobby["timer_task"]:
        config.online_lobby["timer_task"].cancel()
    await bot.send_message(config.online_lobby["creator"], "❌ Лобби отменено.")
    config.online_lobby = None
    await cb.answer("Лобби отменено.")
    await cb.message.edit_text("Лобби отменено.")

async def start_online_game():
    if not config.online_lobby: return
    config.online_lobby["started"] = True
    players = config.online_lobby["players"]
    config.online_lobby["cur"] = 0
    config.online_lobby["rnd"] = 1
    names_line = " ⚔️ ".join(f"*{p['name']}*" for p in players)
    for p in players:
        await bot.send_message(p["chat_id"],
            f"🔥 *ОНЛАЙН-БИТВА НАЧИНАЕТСЯ!*\n\n{names_line}\n\n"
            f"Первый ход: *{players[0]['name']}*", parse_mode="Markdown")
    await push_online_turn(0)

async def push_online_turn(idx: int):
    players = config.online_lobby["players"]
    p = players[idx]
    alive = active_count(players)
    await bot.send_message(p["chat_id"],
        f"🎮 *Раунд {config.online_lobby['rnd']}*  |  Игроков: {alive}\n{'─'*24}\n"
        f"🎯 Твой ход, *{p['name']}*!.",
        parse_mode="Markdown", reply_markup=kb_draw())
    for other in players:
        if other["chat_id"] != p["chat_id"] and not other["out"]:
            await bot.send_message(other["chat_id"], f"⏳ Ход *{p['name']}*...", parse_mode="Markdown")

async def online_draw(cb: CallbackQuery):
    players = config.online_lobby["players"]
    cur = config.online_lobby["cur"]
    if cb.from_user.id != players[cur]["chat_id"]:
        await cb.answer("Сейчас не твой ход!"); return
    suit = random.choice(SUITS)
    rank = random.choice(RANKS)
    count = VALUES[rank]
    players[cur]["total"] += count
    players[cur]["rds"] += 1
    config.online_lobby["last"] = {"suit": suit, "rank": rank, "count": count}
    special = ""
    if rank == "A":
        special = "\n\n⚡ *ТУЗА ВЫТЯНУЛ!* Это сразу 15 раз — держись! 😤"
    elif rank in ("J", "Q", "K"):
        special = "\n\n👑 *Фигурная карта* — 12 раз, не меньше!"
    await cb.message.edit_text(
        f"🃏 *Ты вытянул карту!*\n\n`{card_art(suit, rank, count)}`\n{special}\n\n"
        f"_{suit['tip']}_\n\nСделай *{count}* отжиманий! 💪",
        parse_mode="Markdown", reply_markup=kb_done(),
    )
    for p in players:
        if p["chat_id"] != cb.from_user.id and not p["out"]:
            await bot.send_message(p["chat_id"],
                f"🃏 *{players[cur]['name']}* тянет карту... *{rank} {suit['sym']}* — {count} отж.",
                parse_mode="Markdown")
    await cb.answer("Карта вытянута!")

async def online_done(cb: CallbackQuery):
    players = config.online_lobby["players"]
    cur = config.online_lobby["cur"]
    if cb.from_user.id != players[cur]["chat_id"]:
        await cb.answer("Не твой ход!"); return
    last = config.online_lobby.get("last", {})
    count = last.get("count", 0)
    name = players[cur]["name"]
    await cb.message.edit_text(
        f"✅ Ты сделал *{count}* отж.! Всего у тебя *{players[cur]['total']}*.",
        parse_mode="Markdown")
    await cb.answer("Засчитано!")
    rnd = config.online_lobby["rnd"]
    nxt, new_rnd = next_player(players, cur, rnd)
    config.online_lobby["cur"] = nxt
    config.online_lobby["rnd"] = new_rnd
    if new_rnd > rnd:
        for p in players:
            if not p["out"]:
                await bot.send_message(p["chat_id"],
                    f"🏁 *Раунд {rnd} завершён!*\n\n{make_scoreboard(players)}", parse_mode="Markdown")
    await push_online_turn(nxt)

async def online_score(cb: CallbackQuery):
    await cb.answer()
    await cb.message.answer(
        f"📊 *Раунд {config.online_lobby['rnd']}*\n\n{make_scoreboard(config.online_lobby['players'])}",
        parse_mode="Markdown",
    )

async def online_quit(cb: CallbackQuery):
    players = config.online_lobby["players"]
    user_id = cb.from_user.id
    idx = next((i for i, p in enumerate(players) if p["chat_id"] == user_id), None)
    if idx is None:
        await cb.answer("Ты не в игре."); return
    name = players[idx]["name"]
    players[idx]["out"] = True
    alive = [p for p in players if not p["out"]]
    if len(alive) == 1:
        winner = alive[0]
        for p in players:
            update_player_stats(p["chat_id"], p["name"], {
                "game_type": "online", "won": not p["out"],
                "total_pushups": p["total"], "rounds": p["rds"]
            })
            await bot.send_message(p["chat_id"],
                f"🏳 *{name}* сдался!\n\n🏆 *{winner['name'].upper()} — ПОБЕДИТЕЛЬ!* 🏆\n\n{make_scoreboard(players)}",
                parse_mode="Markdown")
        config.online_lobby = None
    elif len(alive) == 0:
        for p in players:
            await bot.send_message(p["chat_id"], "Все сдались! 😅")
        config.online_lobby = None
    else:
        for p in players:
            await bot.send_message(p["chat_id"],
                f"🏳 *{name}* сдался. Осталось в строю: *{len(alive)}*",
                parse_mode="Markdown")
        if idx == config.online_lobby["cur"]:
            rnd = config.online_lobby["rnd"]
            nxt, new_rnd = next_player(players, idx, rnd)
            config.online_lobby["cur"] = nxt
            config.online_lobby["rnd"] = new_rnd
            await push_online_turn(nxt)
    await cb.answer()

async def online_finish(cb: CallbackQuery):
    players = config.online_lobby["players"]
    rnd = config.online_lobby["rnd"]
    alive = [p for p in players if not p["out"]]
    if alive:
        winner = max(alive, key=lambda x: x["total"])
        for p in players:
            update_player_stats(p["chat_id"], p["name"], {
                "game_type": "online", "won": not p["out"],
                "total_pushups": p["total"], "rounds": p["rds"]
            })
            await bot.send_message(p["chat_id"],
                f"🏁 *ИГРА ЗАВЕРШЕНА!* (Раунд {rnd})\n\n{make_scoreboard(players)}\n\n"
                f"🏆 *{winner['name'].upper()} — ЧЕМПИОН!*", parse_mode="Markdown")
    else:
        for p in players:
            await bot.send_message(p["chat_id"], "Игра завершена, ни одного финишёра.")
    config.online_lobby = None
    await cb.answer("Игра завершена!")

# Обработчик нераспознанных сообщений
@dp.message()
async def fallback(msg: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await msg.answer("Привет! 👋 Нажми /start чтобы начать игру.", reply_markup=kb_main())
