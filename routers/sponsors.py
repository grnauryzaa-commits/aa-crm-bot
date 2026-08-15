from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import psycopg2
from config import DATABASE_URL, ADMINS

router = Router()

class EditSponsorState(StatesGroup):
    waiting_for_new_value = State()

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
    list_type = parts[1]
    page = int(parts[2])
    
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

    PER_PAGE = 5
    total_pages = (len(all_sponsors) + PER_PAGE - 1) // PER_PAGE
    start_idx = page * PER_PAGE
    end_idx = start_idx + PER_PAGE
    current_sponsors = all_sponsors[start_idx:end_idx]

    keyboard = []
    for uid, name in current_sponsors:
        keyboard.append([InlineKeyboardButton(text=name, callback_data=f"view_sp_{uid}_{list_type}_{page}")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"list_{list_type}_{page - 1}"))
    if end_idx < len(all_sponsors):
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"list_{list_type}_{page + 1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Кнопка возврата к выбору категории (Братья / Сестры)
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_sponsors")])

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
        
        keyboard = [
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"list_{list_type}_{page}")]
        ]
        
        current_user_id = callback.from_user.id
        if current_user_id == int(user_id) or current_user_id in ADMINS:
            keyboard.insert(0, [InlineKeyboardButton(text="✏️ Редактировать анкету", callback_data=f"edit_menu_{user_id}_{list_type}_{page}")])

        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data.startswith("edit_menu_"))
async def edit_menu(callback: CallbackQuery):
    parts = callback.data.split("_")
    user_id = parts[2]
    list_type = parts[3]
    page = parts[4]

    if callback.from_user.id != int(user_id) and callback.from_user.id not in ADMINS:
        await callback.answer("⚠️ Вы можете редактировать только свою анкету!", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕊 Срок трезвости", callback_data=f"edit_field_{user_id}_sobriety_{list_type}_{page}")],
        [InlineKeyboardButton(text="📍 Город", callback_data=f"edit_field_{user_id}_city_{list_type}_{page}")],
        [InlineKeyboardButton(text="📞 Телефон", callback_data=f"edit_field_{user_id}_phone_{list_type}_{page}")],
        [InlineKeyboardButton(text="📖 Опыт / Программа", callback_data=f"edit_field_{user_id}_program_info_{list_type}_{page}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"view_sp_{user_id}_{list_type}_{page}")]
    ])
    await callback.message.edit_text("⚙️ Выберите, какое поле вы хотите изменить:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("edit_field_"))
async def start_editing_field(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    user_id = parts[2]
    field_name = parts[3]
    list_type = parts[4]
    page = parts[5]

    if callback.from_user.id != int(user_id) and callback.from_user.id not in ADMINS:
        await callback.answer("⚠️ Доступ запрещен!", show_alert=True)
        return

    await state.update_data(target_user_id=user_id, field_name=field_name, list_type=list_type, page=page)
    await state.set_state(EditSponsorState.waiting_for_new_value)

    field_titles = {
        "sobriety": "новый срок трезвости",
        "city": "новый город",
        "phone": "новый номер телефона",
        "program_info": "новую информацию об опыте"
    }

    await callback.message.answer(f"✍️ Напишите {field_titles.get(field_name, 'новое значение')} в чат:")
    await callback.answer()

@router.message(EditSponsorState.waiting_for_new_value)
async def save_edited_field(message: Message, state: FSMContext):
    new_value = message.text
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    field_name = data.get("field_name")

    allowed_fields = ["sobriety", "city", "phone", "program_info"]
    if field_name not in allowed_fields:
        await message.answer("Ошибка поля.")
        await state.clear()
        return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        query = f"UPDATE sponsors SET {field_name} = %s WHERE user_id = %s;"
        cur.execute(query, (new_value, target_user_id))
        conn.commit()
        cur.close()
        conn.close()

        await message.answer("✅ Данные успешно обновлены!")
        await state.clear()
    except Exception as e:
        print(f"Ошибка при обновлении: {e}")
        await message.answer("❌ Произошла ошибка при сохранении.")
        await state.clear()