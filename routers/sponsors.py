from aiogram import Router, F, types
from database import get_db_connection

router = Router()

@router.message(F.text == "🤝 Спонсоры")
async def show_sponsors(message: types.Message):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, city FROM sponsors WHERE status = 'approved';")
        sponsors = cursor.fetchall()
        cursor.close()
        conn.close()

        if not sponsors:
            await message.answer("На данный момент список спонсоров пуст.")
            return

        text = "📋 Список активных спонсоров:\n\n"
        for sp in sponsors:
            text += f"• {sp['name']} ({sp['city']})\n"
        
        await message.answer(text)
    except Exception as e:
        await message.answer("Произошла ошибка при получении списка спонсоров.")