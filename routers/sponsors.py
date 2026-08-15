from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import psycopg2
from config import DATABASE_URL

router = Router()

# Ловим текстовую кнопку из главного меню нижней клавиатуры
@router.message(F.text == "🤝 Спонсоры")
async def sponsors_text_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👦 Братья", callback_data="list_brothers"),
            InlineKeyboardButton(text="👧 Сестры", callback_data="list_sisters")
        ]
    ])
    await message.answer("👥 Выберите список:", reply_markup=keyboard)

# Ловим callback-кнопку (если она вызывается изнутри)
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

@router.callback_query(F.data == "list_brothers")
async def show_brothers(callback: CallbackQuery):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT name, gender, age, sobriety, city, username, phone, program_info FROM sponsors WHERE gender ILIKE '%брат%';")
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

    except Exception as e:
        print(f"Ошибка при загрузке братьев: {e}")
        await callback.answer("Произошла ошибка при загрузке списка.", show_alert=True)

@router.callback_query(F.data == "list_sisters")
async def show_sisters(callback: CallbackQuery):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT name, gender, age, sobriety, city, username, phone, program_info FROM sponsors WHERE gender ILIKE '%сестр%';")
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

    except Exception as e:
        print(f"Ошибка при загрузке сестер: {e}")
        await callback.answer("Произошла ошибка при загрузке списка.", show_alert=True)