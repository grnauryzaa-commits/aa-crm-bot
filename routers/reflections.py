from aiogram import Router, types
from aiogram.filters import Command
from datetime import datetime
import psycopg2

# Убедитесь, что эта ссылка совпадает с той, что в fill_db.py
DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"

router = Router()

@router.message(lambda message: message.text == "📖 Ежедневные размышления")
@router.message(Command("daily"))
async def send_reflection(message: types.Message):
    # Получаем текущую дату
    today = datetime.now()
    day = today.day
    month = today.month

    try:
        # Подключаемся к базе
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Запрашиваем данные за сегодняшнее число
        cur.execute("""
            SELECT title, text FROM reflections_archive 
            WHERE day = %s AND month = %s
        """, (day, month))
        
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            title, text = row
            # Формируем ответ
            response = f"📖 **{title}**\n\n{text}"
            
            # Отправляем сообщение частями, если оно слишком длинное (Telegram лимит 4096 символов)
            if len(response) > 4096:
                for x in range(0, len(response), 4096):
                    await message.answer(response[x:x+4096])
            else:
                await message.answer(response)
        else:
            await message.answer("Размышление на сегодня пока не найдено в архиве.")
            
    except Exception as e:
        print(f"Ошибка при работе с базой: {e}")
        await message.answer("Произошла ошибка при загрузке размышления. Попробуйте позже.")