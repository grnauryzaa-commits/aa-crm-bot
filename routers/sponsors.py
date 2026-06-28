from aiogram import Router, F, types
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncio
import logging
from config import DATABASE_URL as DB_URL

router = Router()

# Функция для получения списка всех активных и одобренных спонсоров
def _fetch_sponsors_from_db():
    conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    # Берем только тех, кто прошел модерацию и сохранен в основной таблице sponsors
    cur.execute("SELECT name, age, sobriety, city, program_info, username, phone FROM sponsors;")
    sponsors = cur.fetchall()
    cur.close()
    conn.close()
    return sponsors

@router.message(F.text == "🤝 Спонсоры")
async def show_sponsors_list(message: types.Message):
    try:
        # ИСПРАВЛЕНИЕ: Запускаем блокирующую функцию синхронного коннекта в безопасном фоновом потоке асинхронно
        sponsors = await asyncio.to_thread(_fetch_sponsors_from_db)
    except Exception as e:
        # Если что-то пойдет не так, мы увидим реальную причину в логах Railway
        logging.error(f"Критическая ошибка при чтении спонсоров: {e}")
        # Временно выводим текст ошибки в чат, чтобы точно знать, если дело не в асинхронности
        await message.answer(f"⚠️ Ошибка при подключении к базе данных:\n`{str(e)}`", parse_mode="Markdown")
        return

    if not sponsors:
        await message.answer(
            "🕊 **База данных спонсоров группы «Наурыз»**\n\n"
            "В данный момент список пуст. Если вы готовы делиться опытом, силой и надеждой "
            "и хотите стать наставником, нажмите кнопку **«🤝 Стать спонсором»** или **«✍️ Редактировать карточку»** в меню бота!"
        )
        return

    await message.answer(f"🔎 **Найдено доступных спонсоров АА: {len(sponsors)}**\n\nВот актуальный список наставников:")

    # Выводим каждого спонсора отдельной красивой карточкой в стиле Содружества
    for sp in sponsors:
        card_text = (
            "✨ **КАРТОЧКА СПОНСОРА АА**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Имя:** {sp['name']}\n"
            f"📅 **Возраст:** {sp['age']}\n"
            f"🕊 **Трезвость:** {sp['sobriety']}\n"
            f"📍 **Город:** {sp['city']}\n\n"
            f"📖 **Опыт/Программа:** {sp['program_info']}\n"
            f"✈️ **Telegram:** {sp['username']}\n"
            f"📞 **Телефон:** {sp['phone']}\n"
            "━━━━━━━━━━━━━━━━━━"
        )
        await message.answer(card_text, parse_mode="Markdown")