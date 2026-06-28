from aiogram import Router, F, types
import psycopg2
from datetime import datetime
from config import DATABASE_URL as DB_URL

router = Router()

@router.message(F.text == "📖 Ежедневные размышления")
async def show_reflections(message: types.Message):
    day = datetime.now().day
    month = datetime.now().month
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        cur.execute(
            "SELECT title, text FROM reflections_archive WHERE day = %s AND month = %s", 
            (day, month)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            await message.answer(f"📖 **{row[0]}**\n\n{row[1]}")
        else:
            await message.answer("На сегодня размышлений пока нет.")
    except Exception as e:
        await message.answer("Ошибка БД.")
        print(f"Error: {e}")