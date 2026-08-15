from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
import psycopg2
from config import DATABASE_URL

router = Router()

@router.message(F.text == "🤝 Спонсоры")
@router.callback_query(F.data == "menu_sponsors")
async def sponsors_menu(event: Message | CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👦 Братья", callback_data="list_brothers")],
        [InlineKeyboardButton(text="👧 Сестры", callback_data="list_sisters")]
    ])
    if isinstance(event, Message):
        await event.answer("👥 Выберите список:", reply_markup=keyboard)
    else:
        await event.message.edit_text("👥 Выберите список:", reply_markup=keyboard)
        await event.answer()

@router.callback_query(F.data.in_(["list_brothers", "list_sisters"]))
async def show_list(callback: CallbackQuery):
    gender_filter = "OR gender ILIKE '%муж%'" if callback.data == "list_brothers" else "OR gender ILIKE '%жен%'"
    label = "Братья" if callback.data == "list_brothers" else "Сестры"
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(f"SELECT user_id, name FROM sponsors WHERE gender ILIKE '%{label[:4]}%' {gender_filter};")
    sponsors = cur.fetchall()
    cur.close()
    conn.close()

    if not sponsors:
        await callback.answer(f"Список {label} пока пуст.", show_alert=True)
        return

    # Создаем клавиатуру с именами
    keyboard = []
    for uid, name in sponsors:
        keyboard.append([InlineKeyboardButton(text=name, callback_data=f"view_sp_{uid}")])
    keyboard.append([InlineKeyboardButton(text="« Назад", callback_data="menu_sponsors")])

    await callback.message.edit_text(f"📖 Список ({label}):\nНажми на имя, чтобы увидеть детали:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data.startswith("view_sp_"))
async def show_details(callback: CallbackQuery):
    user_id = callback.data.split("_")[2]
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT name, gender, age, sobriety, city, username, phone, program_info FROM sponsors WHERE user_id = %s;", (user_id,))
    sp = cur.fetchone()
    cur.close()
    conn.close()

    if sp:
        name, gender, age, sobriety, city, username, phone, program_info = sp
        text = (f"👤 **{name}** ({gender}), {age} лет\n🕊 Трезвость: {sobriety}\n"
                f"📍 Город: {city}\n📖 Опыт: {program_info}\n"
                f"✈️ Telegram: @{username}\n📞 Телефон: {phone}")
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Назад к списку", callback_data="list_brothers")] # Упрощено
        ]))