import psycopg2
import logging
import asyncio
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import DATABASE_URL as DB_URL

router = Router()

# Синхронная функция получения спонсоров конкретного пола
def _get_sponsors_by_gender(gender: str):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT name, age, sobriety, city, program_info, username, phone 
            FROM sponsors WHERE gender = %s;
        """, (gender,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        logging.error(f"Ошибка получения спонсоров по полу: {e}")
        return []

# 1. Нажатие на главную текстовую кнопку меню "🤝 Спонсоры"
@router.message(F.text == "🤝 Спонсоры")
async def choose_gender(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🙋‍♂️ Братья", callback_data="view_sponsors:Брат:0"),
            InlineKeyboardButton(text="🙋‍♀️ Сестры", callback_data="view_sponsors:Сестра:0")
        ]
    ])
    await message.answer("👥 Чей список спонсоров вы хотите посмотреть?", reply_markup=kb)

# 2. Обработка показа карточек порциями (пагинация по 3 штуки)
@router.callback_query(F.data.startswith("view_sponsors:"))
async def view_sponsors_page(callback: types.CallbackQuery):
    _, gender, offset_str = callback.data.split(":")
    offset = int(offset_str)
    
    # Загружаем спонсоров выбранного пола
    sponsors = await asyncio.to_thread(_get_sponsors_by_gender, gender)
    
    if not sponsors:
        await callback.answer(f"Список активных спонсоров ({gender}ы) пока пуст.", show_alert=True)
        return

    # Настройки лимита вывода
    LIMIT = 3
    chunk = sponsors[offset : offset + LIMIT]
    total = len(sponsors)
    
    if not chunk:
        await callback.answer("Больше анкет нет.", show_alert=True)
        return

    # Удаляем предыдущее инлайн-меню, чтобы не засорять историю чата
    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(f"🔎 Список наставников ({gender}ы). Страница {int(offset/LIMIT)+1}:")
    
    # Построчно выводим карточки из текущей порции
    for row in chunk:
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
        await callback.message.answer(text)

    # Высчитываем следующий шаг пагинации
    next_offset = offset + LIMIT
    inline_buttons = []
    
    # Если в списке ещё остались анкеты, добавляем кнопку "Показать еще"
    if next_offset < total:
        inline_buttons.append(InlineKeyboardButton(text="➡️ Показать еще", callback_data=f"view_sponsors:{gender}:{next_offset}"))
    
    # Кнопка возврата к меню выбора пола
    inline_buttons.append(InlineKeyboardButton(text="🔄 Сменить пол", callback_data="back_to_gender"))
    
    kb = InlineKeyboardMarkup(inline_keyboard=[inline_buttons])
    await callback.message.answer(f"Показано {min(next_offset, total)} из {total} спонсоров.", reply_markup=kb)
    await callback.answer()

# Возврат к первичному выбору пола
@router.callback_query(F.data == "back_to_gender")
async def back_gender(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🙋‍♂️ Братья", callback_data="view_sponsors:Брат:0"),
            InlineKeyboardButton(text="🙋‍♀️ Сестры", callback_data="view_sponsors:Сестра:0")
        ]
    ])
    try:
        await callback.message.edit_text("👥 Чей список спонсоров вы хотите посмотреть?", reply_markup=kb)
    except Exception:
        await callback.message.answer("👥 Чей список спонсоров вы хотите посмотреть?", reply_markup=kb)
    await callback.answer()