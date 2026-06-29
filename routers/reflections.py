import psycopg2
from aiogram import Router, F, types, Bot
from datetime import datetime
import html
import logging

router = Router()

DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@postgres.railway.internal:5432/railway"
CHANNEL_ID = "@aa_nauryz"

def format_reflection_text(title, text, today):
    # Разделяем на [Цитата] и [Текст]
    parts = text.split('***')
    quote_source = parts[0].strip() if len(parts) > 0 else ""
    raw_body = parts[1].strip() if len(parts) > 1 else text
    
    # Жесткая обрезка по конкретной фразе, после которой идет мусор
    clean_body = raw_body.split("...Место под")[0].strip()
    
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", 
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    
    return (
        f"📖 <b>Ежедневные размышления АА</b>\n\n"
        f"📋 <b>{today.day} {months[today.month - 1]}</b>\n\n"
        f"<b>{title.upper()}</b>\n\n"
        f"{html.escape(clean_body)}\n\n"
        f"<i>{html.escape(quote_source)}</i>"
    )

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
            logging.info("Рассылка выполнена.")
    except Exception as e:
        logging.error(f"Ошибка рассылки: {e}")

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
        await message.answer("❌ Ошибка.")