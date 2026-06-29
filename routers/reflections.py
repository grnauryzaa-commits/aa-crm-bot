import psycopg2
from aiogram import Router, F, types, Bot
from datetime import datetime
import html
import logging

router = Router()

DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"
CHANNEL_ID = "@aa_nauryz"

def format_reflection_text(text, today):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    # Мусор, который надо вырезать нафиг
    forbidden = ["WWW.MOS-NACH.RU", "Анонимные Алкоголики.", "Группа", "Поделиться:", 
                 "Рассказать:", "Twitter", "Facebook", "Vkontakte", "WhatsApp", 
                 "Telegram", "EMail", "Тег audio", "Aудио-ежедневник", 
                 "Skype", "Mail", "Альтернативный вариант"]
    
    # Очищаем строки от мусора
    filtered = []
    for line in lines:
        if not any(f in line for f in forbidden):
            # Пропускаем строки с датами, которые дублируются, 
            # чтобы не было каши (кроме заголовка дня)
            if line.strip().lower() == f"{today.day} июня": continue 
            filtered.append(line)
            
    # Собираем тело текста: берем всё, что после заголовка (ЭФФЕКТ ВОЛНЫ и т.д.)
    # Но так как у тебя в примере заголовок статьи идет после даты, 
    # мы просто выводим всё отфильтрованное чисто.
    body = "\n\n".join(filtered)
    
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", 
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    
    return (
        f"📖 <b>Ежедневные размышления АА</b>\n\n"
        f"📋 <b>{today.day} {months[today.month - 1]}</b>\n\n"
        f"{html.escape(body)}"
    )

async def send_daily_reflection_to_channel(bot: Bot):
    today = datetime.now()
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT text FROM reflections_archive WHERE day = %s AND month = %s", 
                    (today.day, today.month))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            text_content = format_reflection_text(row[0], today)
            await bot.send_message(CHANNEL_ID, text_content, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка рассылки: {e}")

@router.message(F.text == "📖 Ежедневные размышления")
async def show_reflections(message: types.Message):
    today = datetime.now()
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT text FROM reflections_archive WHERE day = %s AND month = %s", 
                    (today.day, today.month))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            text = format_reflection_text(row[0], today)
            await message.answer(text, parse_mode="HTML")
        else:
            await message.answer("⚠️ Размышление на сегодня не найдено.")
    except Exception as e:
        logging.error(f"Ошибка вывода: {e}")
        await message.answer("❌ Ошибка при получении размышления.")