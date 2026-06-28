import psycopg2
import logging
import asyncio
from aiogram import Router, F, types
from config import DATABASE_URL as DB_URL

router = Router()

def _get_all_sponsors_sync():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT name, age, sobriety, city, program_info, username, phone 
            FROM sponsors;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        logging.error(f"Ошибка получения списка спонсоров: {e}")
        return []

@router.message(F.text == "🤝 Спонсоры")
async def list_sponsors(message: types.Message):
    sponsors = await asyncio.to_thread(_get_all_sponsors_sync)
    
    if not sponsors:
        await message.answer(
            "🕊 База спонсоров группы «Наурыз»\n\n"
            "В данный момент список спонсоров пуст. "
            "Если ты готов делиться опытом, Шагами и Традициями, нажми кнопку «➕ Стать спонсором»!"
        )
        return

    # Отправляем вводный текст (parse_mode удален во избежание конфликтов со спецсимволами)
    await message.answer(f"🔎 Найдено активных спонсоров АА: {len(sponsors)}\n" + "━" * 18)
    
    for row in sponsors:
        text = (
            f"👤 Имя: {row[0]}\n"
            f"📅 Возраст: {row[1]} лет\n"
            f"🕊 Трезвость: {row[2]}\n"
            f"📍 Город: {row[3]}\n\n"
            f"📖 Опыт: {row[4]}\n"
            f"✈️ Telegram: {row[5]}\n"
            f"📞 Телефон: {row[6]}\n"
            "━━━━━━━━━━━━━━━━━━"
        )
        # Отправляем обычным текстом, теперь никнеймы с нижним подчеркиванием ничего не ломают!
        await message.answer(text)