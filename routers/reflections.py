import os
import psycopg2
from aiogram import Router, F, types, Bot
from datetime import datetime
import html
import logging

router = Router()

# Твой URL базы данных
DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@postgres.railway.internal:5432/railway"
CHANNEL_ID = "@aa_nauryz" # ID твоего канала

def format_reflection_text(title, text, today):
    parts = text.split('***')
    quote = parts[0].strip() if len(parts) > 0 else ""
    raw_body = parts[1].strip() if len(parts) > 1 else ""

    stop_phrases = [
        "Место под", "1990©", "Анонимные Алкоголики", "Группа", 
        "Наша помощь", "Сайт информирует", "Даже когда мы", 
        "Содружество АА", "Основное внимание", "За каждой цитатой",
        "И если хоть одному", "Содержание ее", "В предисловии"
    ]
    
    clean_lines = []
    for line in raw_body.split('\n'):
        line = line.strip()
        if not line: continue
        if any(phrase in line for phrase in stop_phrases):
            break
        clean_lines.append(line)
    
    clean_body = "\n\n".join(clean_lines)
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", 
              "июля", "августа", "сетября", "октября", "ноября", "декабря"]
    
    return (
        f"📖 <b>Ежедневные размышления АА</b>\n\n"
        f"📋 <b>{today.day} {months[today.month - 1]}</b>\n\n"
        f"<b>{title.upper()}</b>\n\n"
        f"<i>«{html.escape(quote)}»</i>\n\n"
        f"{html.escape(clean_body)}"
    )

# Функция для планировщика в main.py
async def send_daily_reflection_to_channel(bot: Bot):
    today = datetime.now()
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT title, text FROM reflections_archive WHERE day = %s AND month = %s", 
                    (today.day, today.month))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            text_content = format_reflection_text(row[0], row[1], today)
            await bot.send_message(CHANNEL_ID, text_content, parse_mode="HTML")
            logging.info("Рассылка в канал выполнена.")
    except Exception as e:
        logging.error(f"Ошибка рассылки: {e}")

# Хэндлер для кнопки
@router.message(F.text == "📖 Ежедневные размышления")
async def show_reflections(message: types.Message):
    today = datetime.now()
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT title, text FROM reflections_archive WHERE day = %s AND month = %s", 
                    (today.day, today.month))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            text = format_reflection_text(row[0], row[1], today)
            await message.answer(text, parse_mode="HTML")
        else:
            await message.answer("⚠️ Размышление на сегодня не найдено.")
    except Exception as e:
        await message.answer("❌ Ошибка загрузки.")