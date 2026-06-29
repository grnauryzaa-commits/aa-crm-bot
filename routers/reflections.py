import os
import psycopg2
from aiogram import Router, types
from aiogram.filters import Command
from datetime import datetime

router = Router()

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway")

@router.message(lambda message: message.text == "📖 Ежедневные размышления")
@router.message(Command("daily"))
async def send_reflection(message: types.Message):
    today = datetime.now()
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT title, text FROM reflections_archive 
            WHERE day = %s AND month = %s
        """, (today.day, today.month))
        
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            title, text = row
            # Разделяем по новому разделителю, который мы задали в fill_db.py
            parts = text.split('|||')
            
            quote = parts[0].strip() if len(parts) > 0 else ""
            body = parts[1].strip() if len(parts) > 1 else ""

            months = [
                "января", "февраля", "марта", "апреля", "мая", "июня", 
                "июля", "августа", "сентября", "октября", "ноября", "декабря"
            ]
            date_str = f"{today.day} {months[today.month - 1]}"

            # Формируем ответ
            response = (
                f"📖 **Ежедневные размышления АА**\n\n"
                f"📋 **{date_str}**\n\n"
                f"**{title}**\n\n"
                f"« *{quote}* »\n\n"
                f"{body}"
            )
            
            await message.answer(response, parse_mode="Markdown")
        else:
            await message.answer("⚠️ Размышление на сегодня пока не найдено.")
            
    except Exception as e:
        print(f"Ошибка БД: {e}")
        await message.answer("❌ Произошла ошибка при доступе к базе данных.")