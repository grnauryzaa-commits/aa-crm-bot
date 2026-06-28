from aiogram import Router, types
from aiogram.filters import Command
from datetime import datetime
import psycopg2
import os

# Используем внутренний адрес Railway для бесплатного трафика
# Если бот запущен в облаке, переменная DATABASE_URL должна быть настроена в Railway Variables
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@postgres.railway.internal:5432/railway")

router = Router()

@router.message(lambda message: message.text == "📖 Ежедневные размышления")
@router.message(Command("daily"))
async def send_reflection(message: types.Message):
    # Получаем текущую дату
    today = datetime.now()
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Запрос к базе данных
        cur.execute("""
            SELECT title, text FROM reflections_archive 
            WHERE day = %s AND month = %s
        """, (today.day, today.month))
        
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            title, text = row
            # Отправляем чистое размышление
            await message.answer(f"📖 **{title}**\n\n{text}")
        else:
            await message.answer("Размышление на сегодня пока не найдено.")
            
    except Exception as e:
        print(f"Ошибка БД: {e}")
        await message.answer("Ошибка доступа к базе данных.")