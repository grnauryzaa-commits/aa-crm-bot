from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import psycopg2
from config import DATABASE_URL

router = Router()

# Ловим текстовую кнопку из главного меню
@router.message(F.text == "🤝 Спонсоры")
async def sponsors_text_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👦 Братья", callback_data="list_brothers"),
            InlineKeyboardButton(text="👧 Сестры", callback_data="list_sisters")
        ]
    ])
    await message.answer("👥 Выберите список:", reply_markup=keyboard)

# Ловим callback-кнопку для меню
@router.callback_query(F.data == "menu_sponsors")
async def sponsors_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👦 Братья", callback_data="list_brothers"),
            InlineKeyboardButton(text="👧 Сестры", callback_data="list_sisters")
        ]
    ])
    await callback.message.edit_text("👥 Выберите список:", reply_markup=keyboard)
    await callback.answer()

# Список Братьев (ищем "брат" или "мужской")
@router.callback_query(F.data == "list_brothers")
async def show_brothers(callback: CallbackQuery):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT name, gender, age, sobriety, city, username, phone, program_info 
            FROM sponsors 
            WHERE gender ILIKE '%брат%' OR gender ILIKE '%муж%';
        """)
        sponsors = cur.fetchall()
        cur.close()
        conn.close()

        if not sponsors:
            await callback.answer("Список Братья пока пуст.", show_alert=True)
            return

        await callback.message.edit_text("👦 **Список спонсоров (Братья):**", reply_markup=None)
        
        for sp in sponsors:
            name, gender, age, sobriety, city, username, phone, program_info = sp
            text = (
                f"👤 **{name}** ({gender}), {age} лет\n"
                f"🕊 Трезвость: {sobriety}\n"
                f"📍 Город: {city}\n"
                f"📖 Опыт: {program_info}\n"
                f"✈️ Telegram: @{username}\n"
                f"📞 Телефон: {phone}"
            )
            await callback.message.answer(text)
        await callback.answer()

    except Exception as e:
        print(f"Ошибка при загрузке братьев: {e}")
        await callback.answer("Ошибка при загрузке.", show_alert=True)

# Список Сестер (ищем "сестр" или "жен")
@router.callback_query(F.data == "list_sisters")
async def show_sisters(callback: CallbackQuery):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT name, gender, age, sobriety, city, username, phone, program_info 
            FROM sponsors 
            WHERE gender ILIKE '%сестр%' OR gender ILIKE '%жен%';
        """)
        sponsors = cur.fetchall()
        cur.close()
        conn.close()

        if not sponsors:
            await callback.answer("Список Сестры пока пуст.", show_alert=True)
            return

        await callback.message.edit_text("👧 **Список спонсоров (Сестры):**", reply_markup=None)
        
        for sp in sponsors:
            name, gender, age, sobriety, city, username, phone, program_info = sp
            text = (
                f"👤 **{name}** ({gender}), {age} лет\n"
                f"🕊 Трезвость: {sobriety}\n"
                f"📍 Город: {city}\n"
                f"📖 Опыт: {program_info}\n"
                f"✈️ Telegram: @{username}\n"
                f"📞 Телефон: {phone}"
            )
            await callback.message.answer(text)
        await callback.answer()

    except Exception as e:
        print(f"Ошибка при загрузке сестер: {e}")
        await callback.answer("Ошибка при загрузке.", show_alert=True)