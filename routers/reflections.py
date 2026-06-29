import os
import psycopg2
from aiogram import Router, types
from aiogram.filters import Command
from datetime import datetime
import html

router = Router()

DB_URL = os.getenv("DATABASE_URL")

@router.message(lambda message: message.text == "📖 Ежедневные размышления")
@router.message(Command("daily"))
async def send_reflection(message: types.Message):
    if not DB_URL:
        await message.answer("❌ Ошибка: переменная DATABASE_URL не найдена.")
        return

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
            parts = text.split('***') # Разделитель из твоего fill_db.py
            quote = parts[0].strip() if len(parts) > 0 else ""
            body = parts[1].strip() if len(parts) > 1 else ""

            months = [
                "января", "февраля", "марта", "апреля", "мая", "июня", 
                "июля", "августа", "сентября", "октября", "ноября", "декабря"
            ]
            
            # Используем HTML-теги, они не требуют экранирования точек
            response = (
                f"📖 <b>Ежедневные размышления АА</b>\n\n"
                f"📋 <b>{today.day} {months[today.month - 1]}</b>\n\n"
                f"<b>{html.escape(title)}</b>\n\n"
                f"<i>« {html.escape(quote)} »</i>\n\n"
                f"{html.escape(body)}"
            )

            # Обрезаем, если текст слишком большой
            if len(response) > 4000:
                response = response[:3997] + "..."

            await message.answer(response, parse_mode="HTML")
        else:
            await message.answer(f"⚠️ Размышление на {today.day} {months[today.month-1]} не найдено.")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)[:100]}")