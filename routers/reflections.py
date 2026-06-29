import os
import psycopg2
from aiogram import Router, types
from aiogram.filters import Command
from datetime import datetime

router = Router()

# Получаем URL из переменных окружения
DB_URL = os.getenv("DATABASE_URL")

@router.message(lambda message: message.text == "📖 Ежедневные размышления")
@router.message(Command("daily"))
async def send_reflection(message: types.Message):
    if not DB_URL:
        await message.answer("❌ Ошибка: переменная DATABASE_URL не найдена.")
        return

    today = datetime.now()
    
    try:
        # Убираем sslmode, если он вызывает ошибку, и пробуем простое подключение
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Запрос к таблице
        cur.execute("""
            SELECT title, text FROM reflections_archive 
            WHERE day = %s AND month = %s
        """, (today.day, today.month))
        
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            title, text = row
            # Разделяем по нашему разделителю
            parts = text.split('|||')
            quote = parts[0].strip() if len(parts) > 0 else ""
            body = parts[1].strip() if len(parts) > 1 else ""

            months = [
                "января", "февраля", "марта", "апреля", "мая", "июня", 
                "июля", "августа", "сентября", "октября", "ноября", "декабря"
            ]
            
            response = (
                f"📖 **Ежедневные размышления АА**\n\n"
                f"📋 **{today.day} {months[today.month - 1]}**\n\n"
                f"**{title}**\n\n"
                f"« *{quote}* »\n\n"
                f"{body}"
            )
            await message.answer(response, parse_mode="Markdown")
        else:
            await message.answer(f"⚠️ Размышление на {today.day} {months[today.month-1]} не найдено в базе.")
            
    except Exception as e:
        # Выводим конкретную ошибку, чтобы понять причину
        error_text = f"❌ Ошибка базы: {str(e)}"
        print(error_text)
        await message.answer(error_text)