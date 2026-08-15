from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
import psycopg2
from config import DATABASE_URL

router = Router()

@router.message(F.text == "🤝 Спонсоры")
@router.callback_query(F.data == "menu_sponsors")
async def sponsors_menu(event: Message | CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👦 Братья", callback_data="list_brothers_0")],
        [InlineKeyboardButton(text="👧 Сестры", callback_data="list_sisters_0")]
    ])
    if isinstance(event, Message):
        await event.answer("👥 Выберите список:", reply_markup=keyboard)
    else:
        await event.message.edit_text("👥 Выберите список:", reply_markup=keyboard)
        await event.answer()

@router.callback_query(F.data.startswith(("list_brothers_", "list_sisters_")))
async def show_list_page(callback: CallbackQuery):
    parts = callback.data.split("_")
    list_type = parts[1]  # brothers или sisters
    page = int(parts[2])  # номер страницы
    
    gender_filter = "OR gender ILIKE '%муж%'" if list_type == "brothers" else "OR gender ILIKE '%жен%'"
    label = "Братья" if list_type == "brothers" else "Сестры"
    db_keyword = "брат" if list_type == "brothers" else "сестр"

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(f"SELECT user_id, name FROM sponsors WHERE gender ILIKE '%{db_keyword}%' {gender_filter};")
    all_sponsors = cur.fetchall()
    cur.close()
    conn.close()

    if not all_sponsors:
        await callback.answer(f"Список {label} пока пуст.", show_alert=True)
        return

    PER_PAGE = 5  # Количество спонсоров на одной странице
    total_pages = (len(all_sponsors) + PER_PAGE - 1) // PER_PAGE
    
    start_idx = page * PER_PAGE
    end_idx = start_idx + PER_PAGE
    current_sponsors = all_sponsors[start_idx:end_idx]

    keyboard = []
    for uid, name in current_sponsors:
        keyboard.append([InlineKeyboardButton(text=name, callback_data=f"view_sp_{uid}_{list_type}_{page}")])

    # Кнопки пагинации (Вперед / Назад)
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"list_{list_type}_{page - 1}"))
    if end_idx < len(all_sponsors):
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"list_{list_type}_{page + 1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton(text="« Главное меню", callback_data="menu_sponsors")])

    await callback.message.edit_text(
        f"📖 Список ({label}) — Страница {page + 1} из {total_pages}:\nНажми на имя для просмотра деталей:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(F.data.startswith("view_sp_"))
async def show_details(callback: CallbackQuery):
    parts = callback.data.split("_")
    user_id = parts[2]
    list_type = parts[3]
    page = parts[4]

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
            [InlineKeyboardButton(text="« К списку", callback_data=f"list_{list_type}_{page}")]
        ]))