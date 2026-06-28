from aiogram import Router, F, types
import psycopg2
from datetime import datetime
from config import DATABASE_URL as DB_URL

router = Router()

@router.message(F.text == "📖 Ежедневные размышления")
async def show_reflections(message: types.Message):
    # Получаем текущую дату
    now = datetime.now()
    day = now.day
    month = now.month
    
    try:
        # Используем psycopg2 напрямую, как в твоем database.py
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Ищем запись по дню и месяцу
        cur.execute(
            "SELECT title, text FROM reflections_archive WHERE day = %s AND month = %s", 
            (day, month)
        )
        row = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if row:
            title, text = row
            await message.answer(f"📖 **{title}**\n\n{text}")
        else:
            await message.answer("На сегодня размышлений в базе не найдено. Попробуйте позже.")
            
    except Exception as e:
        await message.answer("⚠️ Ошибка при подключении к архиву размышлений.")
        print(f"Database error: {e}")