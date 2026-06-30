import psycopg2
from aiogram import Router, F, types, Bot
from datetime import datetime
import html
import logging

router = Router()

DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"
# Замени на свой цифровой ID канала, если юзернейм продолжает глючить
CHANNEL_ID = "@aa_nauryz" 

def format_reflection_text(text, today):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    forbidden = [
        "WWW.MOS-NACH.RU", "Анонимные Алкоголики.", "Группа", "Поделиться:", 
        "Рассказать:", "Twitter", "Facebook", "Vkontakte", "WhatsApp", 
        "Telegram", "EMail", "Тег audio", "Aудио-ежедневник", 
        "Skype", "Mail", "Альтернативный вариант",
        "Ежедневные Размышления на", "Сегодня"
    ]
    
    filtered = []
    for line in lines:
        if any(f in line for f in forbidden):
            continue
        if f"{today.day}" in line and "июня" in line.lower() and len(line) < 20:
            continue
        filtered.append(line)
    
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
        else:
            logging.error("Размышление на сегодня не найдено в базе.")
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

@router.message(F.text == "/test_send")
async def test_send(message: types.Message, bot: Bot):
    await message.answer("Попытка запуска тестовой рассылки...")
    try:
        await send_daily_reflection_to_channel(bot)
        await message.answer("Рассылка успешно выполнена!")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
        logging.error(f"Тест рассылки упал: {e}")