import psycopg2
from aiogram import Router, F, types, Bot
from datetime import datetime
import html
import logging

router = Router()

DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"
CHANNEL_ID = "@aa_nauryz"

def format_reflection_text(title, text, today):
    # Очистка мусора
    bad_phrases = ["Поделиться:", "Рассказать:", "Aудио-ежедневник", "Тег audio", 
                   "Twitter", "Facebook", "Vkontakte", "WhatsApp", "Telegram", "EMail"]
    
    clean_text = text
    for phrase in bad_phrases:
        clean_text = clean_text.split(phrase)[0]
    
    # Если заголовок попал в текст, вырезаем его, чтобы не дублировать
    if title in clean_text:
        clean_text = clean_text.split(title, 1)[1]
    
    # Принудительная вставка пустых строк для красоты (если их мало)
    # Заменяем цепочки пробелов на одинарный пробел, сохраняя переносы
    clean_text = "\n".join([line.strip() for line in clean_text.split('\n') if line.strip()])
    
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", 
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    
    return (
        f"📖 <b>Ежедневные размышления АА</b>\n\n"
        f"📋 <b>{today.day} {months[today.month - 1]}</b>\n\n"
        f"<b>{title.upper()}</b>\n\n"
        f"{html.escape(clean_text)}"
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
        logging.error(f"Ошибка вывода: {e}")
        await message.answer("❌ Ошибка при получении размышления.")