import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import (
Application, CommandHandler, MessageHandler, ConversationHandler,
ContextTypes, filters
)

# Файл, где будут сохраняться записи дневника

DIARY_FILE = “diary_data.json”

# ID стикера (твой)

STICKER_ID = “CAACAgQAAxkBAAEQY2ZpfebQk4Af9-103htwFhoVEm-H7gACugwAAksGmFH416EKFkWuhDgE”

# Этапы диалога

CHOOSING_ACTION = 1
ADDING_GOOD = 2
ADDING_BETTER = 3
ADDING_TIKTOK = 4
ADDING_READ = 5
ADDING_SLEEP = 6

# Загрузка данных из файла

def load_diary():
if os.path.exists(DIARY_FILE):
with open(DIARY_FILE, “r”, encoding=“utf-8”) as f:
return json.load(f)
return {}

# Сохранение данных в файл

def save_diary(data):
with open(DIARY_FILE, “w”, encoding=“utf-8”) as f:
json.dump(data, f, ensure_ascii=False, indent=2)

# Экранирование спецсимволов для Markdown V2

def escape_markdown(text):
“”“Экранируем специальные символы для Markdown V2”””
special_chars = [’_’, ‘*’, ‘[’, ‘]’, ‘(’, ‘)’, ‘~’, ‘`’, ‘>’, ‘#’, ‘+’, ‘-’, ‘=’, ‘|’, ‘{’, ‘}’, ‘.’, ‘!’]
for char in special_chars:
text = text.replace(char, f’\{char}’)
return text

# КОМАНДА: /start

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Стартовая команда”””
# Отправляем стикер
await update.message.reply_sticker(STICKER_ID)

```
keyboard = [
    ["📝 Добавить запись", "📊 Статистика"],
    ["📖 История", "❌ Выход"]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Красивое сообщение на Markdown V2
welcome_text = (
    "*🎯 Добро пожаловать в твой личный дневник\\!*\n\n"
    "_Этот бот поможет тебе отслеживать прогресс и изменять жизнь_\n\n"
    "*Что ты хочешь сделать\\?*"
)

await update.message.reply_text(
    welcome_text,
    reply_markup=reply_markup,
    parse_mode=ParseMode.MARKDOWN_V2
)
return CHOOSING_ACTION
```

# КОМАНДА: Главное меню

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Возврат в главное меню”””
keyboard = [
[“📝 Добавить запись”, “📊 Статистика”],
[“📖 История”, “❌ Выход”]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

```
menu_text = (
    "*Вернулись в главное меню*\n\n"
    "_Выбери действие_"
)

await update.message.reply_text(
    menu_text,
    reply_markup=reply_markup,
    parse_mode=ParseMode.MARKDOWN_V2
)
return CHOOSING_ACTION
```

# ДЕЙСТВИЕ: Добавить запись

async def add_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Начало добавления записи”””
# Отправляем стикер
await update.message.reply_sticker(STICKER_ID)

```
context.user_data['date'] = datetime.now().strftime("%Y\\-m\\-d")
context.user_data['entry'] = {}

date_display = datetime.now().strftime("%Y-%m-%d")

prompt_text = (
    f"*📝 Новая запись на {escape_markdown(date_display)}*\n\n"
    "*Что ХОРОШЕГО ты сделал сегодня\\?*\n"
    "_(Максимум 3 пункта, разделяй запятой)_\n\n"
    "`Пример:`\n"
    "_Не спал в TikTok, прочитал 20 страниц, поговорил с папой_"
)

await update.message.reply_text(
    prompt_text,
    reply_markup=ReplyKeyboardRemove(),
    parse_mode=ParseMode.MARKDOWN_V2
)
return ADDING_GOOD
```

# ЭТАП 1: Хорошее

async def adding_good(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Записываем хорошее”””
context.user_data[‘entry’][‘good’] = update.message.text

```
good_text = (
    "*✅ Записал\\!*\n\n"
    "*Что ты УЛУЧШИШЬ завтра\\?*\n"
    "_(Максимум 2 пункта)_\n\n"
    "`Пример:`\n"
    "_Буду спать раньше, не буду откладывать ДЗ_"
)

await update.message.reply_text(
    good_text,
    parse_mode=ParseMode.MARKDOWN_V2
)
return ADDING_BETTER
```

# ЭТАП 2: Что улучшить

async def adding_better(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Записываем, что улучшить”””
context.user_data[‘entry’][‘better’] = update.message.text

```
better_text = (
    "*💡 Понял\\!*\n\n"
    "*Сколько МИНУТ ты был в TikTok сегодня\\?*\n"
    "_(Напиши число, например: 120)_"
)

await update.message.reply_text(
    better_text,
    parse_mode=ParseMode.MARKDOWN_V2
)
return ADDING_TIKTOK
```

# ЭТАП 3: TikTok время

async def adding_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Записываем TikTok время”””
try:
tiktok_mins = int(update.message.text)
context.user_data[‘entry’][‘tiktok’] = tiktok_mins

```
    # Анализ TikTok времени
    if tiktok_mins > 180:
        emoji = "🔴"
        analysis = f"_Это {tiktok_mins // 60} часов {tiktok_mins % 60} минут\\. ОЧЕНЬ много\\._"
    elif tiktok_mins > 60:
        emoji = "🟡"
        analysis = f"_{tiktok_mins} минут\\. Нужно меньше\\._"
    else:
        emoji = "🟢"
        analysis = f"_{tiktok_mins} минут\\. Отлично\\!_"
    
    tiktok_text = (
        f"*{emoji} {analysis}*\n\n"
        "*Сколько СТРАНИЦ ты прочитал сегодня\\?*\n"
        "_(Напиши число или 0, если не читал)_"
    )
    
    await update.message.reply_text(
        tiktok_text,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return ADDING_READ
except ValueError:
    error_text = "*❌ Напиши число\\!* `Например: 120`"
    await update.message.reply_text(
        error_text,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return ADDING_TIKTOK
```

# ЭТАП 4: Чтение

async def adding_read(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Записываем, сколько страниц прочитал”””
try:
pages = int(update.message.text)
context.user_data[‘entry’][‘read’] = pages

```
    # Анализ чтения
    if pages > 30:
        emoji = "🟢"
        analysis = f"_{pages} страниц\\! Супер\\!_"
    elif pages > 10:
        emoji = "🟡"
        analysis = f"_{pages} страниц\\. Хорошо\\._"
    elif pages > 0:
        emoji = "🟢"
        analysis = f"_{pages} страниц\\. Продолжай\\!_"
    else:
        emoji = "🔴"
        analysis = "_0 страниц\\. Нужно читать больше\\._"
    
    read_text = (
        f"*{emoji} {analysis}*\n\n"
        "*Сколько ЧАСОВ ты спал сегодня\\?*\n"
        "_(Напиши число, например: 8)_"
    )
    
    await update.message.reply_text(
        read_text,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return ADDING_SLEEP
except ValueError:
    error_text = "*❌ Напиши число\\!* `Например: 20`"
    await update.message.reply_text(
        error_text,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return ADDING_READ
```

# ЭТАП 5: Сон

async def adding_sleep(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Записываем, сколько спал”””
try:
sleep_hours = float(update.message.text)
context.user_data[‘entry’][‘sleep’] = sleep_hours

```
    # Анализ сна
    if sleep_hours >= 7.5:
        emoji = "🟢"
        analysis = f"_{sleep_hours} часов\\. Отлично спал\\!_"
    elif sleep_hours >= 6:
        emoji = "🟡"
        analysis = f"_{sleep_hours} часов\\. Маловато\\._"
    else:
        emoji = "🔴"
        analysis = f"_{sleep_hours} часов\\. Очень мало для развития мозга\\!_"
    
    # Сохраняем запись
    diary = load_diary()
    date = datetime.now().strftime("%Y-%m-%d")
    diary[date] = context.user_data['entry']
    save_diary(diary)
    
    # Показываем итоговую запись
    entry = context.user_data['entry']
    
    # Экранируем текст для Markdown V2
    good_escaped = escape_markdown(entry['good'][:100])  # Первые 100 символов
    better_escaped = escape_markdown(entry['better'][:100])
    
    summary = (
        f"*{emoji} {analysis}*\n\n"
        f"*✅ Запись сохранена\\!*\n\n"
        f"*📋 ИТОГО на {date}:*\n"
        f"*✅ Хорошее:*\n_{good_escaped}_\n\n"
        f"*⚠️ Улучшить:*\n_{better_escaped}_\n\n"
        f"*📊 TikTok:* `{entry['tiktok']} мин`\n"
        f"*📚 Прочитал:* `{entry['read']} стр`\n"
        f"*💤 Спал:* `{entry['sleep']} ч`"
    )
    
    # Отправляем стикер
    await update.message.reply_sticker(STICKER_ID)
    
    await update.message.reply_text(
        summary,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    await main_menu(update, context)
    
except ValueError:
    error_text = "*❌ Напиши число\\!* `Например: 8`"
    await update.message.reply_text(
        error_text,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return ADDING_SLEEP
```

# СТАТИСТИКА

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Показываем статистику”””
# Отправляем стикер
await update.message.reply_sticker(STICKER_ID)

```
diary = load_diary()

if not diary:
    stats_empty = (
        "*📊 Дневник пуст*\n\n"
        "_Добавь первую запись\\!_"
    )
    await update.message.reply_text(
        stats_empty,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    await main_menu(update, context)
    return CHOOSING_ACTION

# Считаем статистику
tiktok_total = sum(entry.get('tiktok', 0) for entry in diary.values())
read_total = sum(entry.get('read', 0) for entry in diary.values())
sleep_total = sum(entry.get('sleep', 0) for entry in diary.values())
sleep_avg = sleep_total / len(diary) if diary else 0
entries_count = len(diary)

# Среднее TikTok в день
tiktok_avg = tiktok_total // entries_count if entries_count > 0 else 0

# Анализ
stats_text = (
    "*📊 СТАТИСТИКА*\n\n"
    f"*Дней записей:* `{entries_count}`\n"
    f"*📱 TikTok всего:* `{tiktok_total} мин` `({tiktok_avg} мин/день)`\n"
    f"*📚 Прочитано:* `{read_total} страниц`\n"
    f"*💤 Спал всего:* `{sleep_total:.1f} часов` `({sleep_avg:.1f} ч/день)`\n\n"
)

# Оценка
if tiktok_avg <= 60:
    stats_text += "> 🟢 *TikTok под контролем\\!*\n"
elif tiktok_avg <= 120:
    stats_text += "> 🟡 *TikTok можно меньше*\n"
else:
    stats_text += "> 🔴 *TikTok слишком много\\!*\n"

if read_total > entries_count * 10:
    stats_text += "> 🟢 *Хорошо читаешь\\!*\n"

if sleep_avg >= 7.5:
    stats_text += "> 🟢 *Сон в норме\\!*"
else:
    stats_text += "> 🟡 *Нужно спать больше*"

await update.message.reply_text(
    stats_text,
    parse_mode=ParseMode.MARKDOWN_V2
)
await main_menu(update, context)
return CHOOSING_ACTION
```

# ИСТОРИЯ

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Показываем последние записи”””
# Отправляем стикер
await update.message.reply_sticker(STICKER_ID)

```
diary = load_diary()

if not diary:
    history_empty = (
        "*📖 История пуста*\n\n"
        "_Добавь первую запись\\!_"
    )
    await update.message.reply_text(
        history_empty,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    await main_menu(update, context)
    return CHOOSING_ACTION

# Сортируем по дате (новые сверху)
sorted_dates = sorted(diary.keys(), reverse=True)[:7]  # Последние 7 дней

history_text = "*📖 ПОСЛЕДНИЕ ЗАПИСИ*\n\n"

for i, date in enumerate(sorted_dates, 1):
    entry = diary[date]
    good_short = escape_markdown(entry.get('good', '-')[:50])
    
    history_text += (
        f"*{i}\\. 📅 {date}*\n"
        f"✅ _{good_short}_\n"
        f"📊 TikTok: `{entry.get('tiktok', 0)} мин` | "
        f"📚 Читал: `{entry.get('read', 0)} стр` | "
        f"💤 Спал: `{entry.get('sleep', 0)} ч`\n\n"
    )

await update.message.reply_text(
    history_text,
    parse_mode=ParseMode.MARKDOWN_V2
)
await main_menu(update, context)
return CHOOSING_ACTION
```

# ВЫХОД

async def exit_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Выход”””
exit_text = (
“*👋 До встречи\!*\n\n”
“*Продолжай развиваться\!*\n\n”
“Напиши `/start`, чтобы начать снова\.”
)

```
await update.message.reply_text(
    exit_text,
    reply_markup=ReplyKeyboardRemove(),
    parse_mode=ParseMode.MARKDOWN_V2
)
return ConversationHandler.END
```

# ОБРАБОТКА ВЫБОРА ДЕЙСТВИЯ

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Обработка выбора в главном меню”””
text = update.message.text

```
if text == "📝 Добавить запись":
    return await add_entry(update, context)
elif text == "📊 Статистика":
    return await show_stats(update, context)
elif text == "📖 История":
    return await show_history(update, context)
elif text == "❌ Выход":
    return await exit_bot(update, context)
else:
    unknown_text = (
        "*❌ Неизвестная команда*\n\n"
        "_Выбери из меню\\._"
    )
    await update.message.reply_text(
        unknown_text,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return CHOOSING_ACTION
```

# ГЛАВНАЯ ФУНКЦИЯ

def main():
“”“Запуск бота”””
# ТУТ ВСТАВЛЯЙ СВОЙ TOKEN (получи у @BotFather в Telegram)
TOKEN = “8570911226:AAEfa7tZquibcUh8HzCOrxZBQ-a5vwH84kA”

```
if TOKEN == "ВСТАВЬ_СВОЙ_TOKEN_ЗДЕСЬ":
    print("❌ ОШИБКА: Замени TOKEN на свой! (получи у @BotFather)")
    return

# Создаём приложение (это основной класс бота)
app = Application.builder().token(TOKEN).build()

# Создаём ConversationHandler (это управляет диалогом)
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSING_ACTION: [MessageHandler(filters.TEXT, handle_choice)],
        ADDING_GOOD: [MessageHandler(filters.TEXT, adding_good)],
        ADDING_BETTER: [MessageHandler(filters.TEXT, adding_better)],
        ADDING_TIKTOK: [MessageHandler(filters.TEXT, adding_tiktok)],
        ADDING_READ: [MessageHandler(filters.TEXT, adding_read)],
        ADDING_SLEEP: [MessageHandler(filters.TEXT, adding_sleep)],
    },
    fallbacks=[CommandHandler("start", start)],
)

# Добавляем обработчик
app.add_handler(conv_handler)

# Запускаем бота
print("✅ Бот запущен! Нажми Ctrl+C для остановки.")
app.run_polling()
```

if **name** == “**main**”:
main()
