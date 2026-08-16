from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import psycopg2
from config import DATABASE_URL, ADMINS

router = Router()

# ==========================================
# СОСТОЯНИЯ ДЛЯ РЕГИСТРАЦИИ СПОНСОРА (FSM)
# ==========================================
class RegisterSponsorState(StatesGroup):
    waiting_for_name = State()
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_sobriety = State()
    waiting_for_city = State()
    waiting_for_phone = State()
    waiting_for_program_info = State()

# Состояния для редактирования существующей анкеты
class EditSponsorState(StatesGroup):
    waiting_for_new_value = State()

# ==========================================
# ШАГ 1: НАЖАТИЕ КНОПКИ «➕ Стать спонсором»
# ==========================================
@router.message(F.text == "➕ Стать спонсором")
async def start_sponsor_registration(message: Message, state: FSMContext):
    # Устанавливаем первое состояние и запрашиваем имя
    await state.set_state(RegisterSponsorState.waiting_for_name)
    await message.answer(
        "➕ <b>Регистрация в качестве спонсора</b>\n\n"
        "Пожалуйста, введите ваше имя (или как к вам обращаться):",
        parse_mode="HTML"
    )

# ==========================================
# ШАГ 2: ПОЛУЧЕНИЕ ИМЕНИ И ЗАПРОС ПОЛА
# ==========================================
@router.message(RegisterSponsorState.waiting_for_name)
async def process_sponsor_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(RegisterSponsorState.waiting_for_gender)
    
    # Инлайн-кнопки для выбора пола/направления
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👦 Брат (Мужской)", callback_data="gender_brother")],
        [InlineKeyboardButton(text="👧 Сестра (Женский)", callback_data="gender_sister")]
    ])
    await message.answer("Выберите ваш пол / направление:", reply_markup=keyboard)

# ==========================================
# ШАГ 3: ПОЛУЧЕНИЕ ПОЛА И ЗАПРОС ВОЗРАСТА
# ==========================================
@router.callback_query(RegisterSponsorState.waiting_for_gender, F.data.startswith("gender_"))
async def process_sponsor_gender(callback: CallbackQuery, state: FSMContext):
    gender_val = "Брат (Мужской)" if callback.data == "gender_brother" else "Сестра (Женский)"
    await state.update_data(gender=gender_val)
    await state.set_state(RegisterSponsorState.waiting_for_age)
    await callback.message.edit_text("Введите ваш возраст (только цифры от 18 до 100):")
    await callback.answer()

# ==========================================
# ШАГ 4: ПОЛУЧЕНИЕ ВОЗРАСТА И ЗАПРОС ТРЕЗВОСТИ
# ==========================================
@router.message(RegisterSponsorState.waiting_for_age)
async def process_sponsor_age(message: Message, state: FSMContext):
    if not message.text.strip().isdigit() or not (18 <= int(message.text.strip()) <= 100):
        await message.answer("⚠️ Возраст должен быть числом от 18 до 100. Попробуйте еще раз:")
        return
    await state.update_data(age=int(message.text.strip()))
    await state.set_state(RegisterSponsorState.waiting_for_sobriety)
    await message.answer("Введите ваш срок трезвости (например: <i>3 года 5 месяцев</i> или <i>1 год</i>):", parse_mode="HTML")

# ==========================================
# ШАГ 5: ПОЛУЧЕНИЕ ТРЕЗВОСТИ И ЗАПРОС ГОРОДА
# ==========================================
@router.message(RegisterSponsorState.waiting_for_sobriety)
async def process_sponsor_sobriety(message: Message, state: FSMContext):
    await state.update_data(sobriety=message.text.strip())
    await state.set_state(RegisterSponsorState.waiting_for_city)
    await message.answer("Укажите ваш город:")

# ==========================================
# ШАГ 6: ПОЛУЧЕНИЕ ГОРОДА И ЗАПРОС ТЕЛЕФОНА
# ==========================================
@router.message(RegisterSponsorState.waiting_for_city)
async def process_sponsor_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text.strip())
    await state.set_state(RegisterSponsorState.waiting_for_phone)
    await message.answer("Укажите ваш контактный телефон (или мессенджер):")

# ==========================================
# ШАГ 7: ПОЛУЧЕНИЕ ТЕЛЕФОНА И ЗАПРОС ОПЫТА
# ==========================================
@router.message(RegisterSponsorState.waiting_for_phone)
async def process_sponsor_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await state.set_state(RegisterSponsorState.waiting_for_program_info)
    await message.answer("Напишите краткую информацию о вашем прохождении программы / опыте спонсорства:")

# ==========================================
# ШАГ 8: СОХРАНЕНИЕ ВСЕЙ АНКЕТЫ В БАЗУ ДАННЫХ
# ==========================================
@router.message(RegisterSponsorState.waiting_for_program_info)
async def process_sponsor_program_info(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "-"

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        # Запись в БД или обновление, если юзер уже был зарегистрирован
        cur.execute(
            """
            INSERT INTO sponsors (user_id, name, gender, age, sobriety, city, username, phone, program_info)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                name = EXCLUDED.name,
                gender = EXCLUDED.gender,
                age = EXCLUDED.age,
                sobriety = EXCLUDED.sobriety,
                city = EXCLUDED.city,
                username = EXCLUDED.username,
                phone = EXCLUDED.phone,
                program_info = EXCLUDED.program_info;
            """,
            (
                user_id,
                data.get("name"),
                data.get("gender"),
                data.get("age"),
                data.get("sobriety"),
                data.get("city"),
                username,
                data.get("phone"),
                message.text.strip()
            )
        )
        conn.commit()
        cur.close()
        conn.close()

        await message.answer("✅ <b>Вы успешно зарегистрированы в базе спонсоров!</b>", parse_mode="HTML")
        await state.clear()
    except Exception as e:
        print(f"Ошибка сохранения спонсора: {e}")
        await message.answer("❌ Произошла ошибка при сохранении анкеты в базу данных.")
        await state.clear()

# ==========================================
# ПРОСМОТР СПИСКА СПОНСОРОВ (Братья / Сестры)
# ==========================================
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

# ==========================================
# ПАГИНАЦИЯ И ОТОБРАЖЕНИЕ СТРАНИЦ СПИСКА
# ==========================================
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
    cur.execute(f"SELECT user_id, name, age, city, sobriety FROM sponsors WHERE gender ILIKE '%{db_keyword}%' {gender_filter};")
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
    for uid, name, age, city, sobriety in current_sponsors:
        button_text = f"{name}, {age} лет | {city or 'Город'} | {sobriety}"
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"view_sp_{uid}_{list_type}_{page}")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"list_{list_type}_{page - 1}"))
    if end_idx < len(all_sponsors):
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"list_{list_type}_{page + 1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_sponsors")])

    await callback.message.edit_text(
        f"📖 Список ({label}) — Страница {page + 1} из {total_pages}:\nНажми на спонсора для просмотра деталей:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

# ==========================================
# ПРОСМОТР ДЕТАЛЕЙ КОНКРЕТНОГО СПОНСОРА
# ==========================================
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
        
        if username and username != "-":
            tg_contact = f"@{username}"
        else:
            tg_contact = f"[Написать в личку](tg://user?id={user_id})"

        text = (f"👤 **{name}** ({gender}), {age} лет\n🕊 Трезвость: {sobriety}\n"
                f"📍 Город: {city}\n📖 Опыт: {program_info}\n"
                f"✈️ Telegram: {tg_contact}\n📞 Телефон: {phone}")
        
        keyboard = [
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"list_{list_type}_{page}")]
        ]
        
        current_user_id = callback.from_user.id
        if current_user_id == int(user_id) or current_user_id in ADMINS:
            keyboard.insert(0, [InlineKeyboardButton(text="✏️ Редактировать анкету", callback_data=f"edit_menu_{user_id}_{list_type}_{page}")])

        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

# ==========================================
# МЕНЮ РЕДАКТИРОВАНИЯ АНКЕТЫ
# ==========================================
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
        [InlineKeyboardButton(text="📅 Возраст", callback_data=f"edit_field_{user_id}_age_{list_type}_{page}")],
        [InlineKeyboardButton(text="🕊 Срок трезвости", callback_data=f"edit_field_{user_id}_sobriety_{list_type}_{page}")],
        [InlineKeyboardButton(text="📍 Город", callback_data=f"edit_field_{user_id}_city_{list_type}_{page}")],
        [InlineKeyboardButton(text="📞 Телефон", callback_data=f"edit_field_{user_id}_phone_{list_type}_{page}")],
        [InlineKeyboardButton(text="📖 Опыт / Программа", callback_data=f"edit_field_{user_id}_programinfo_{list_type}_{page}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"view_sp_{user_id}_{list_type}_{page}")]
    ])
    await callback.message.edit_text("⚙️ Выберите, какое поле вы хотите изменить:", reply_markup=keyboard)

# ==========================================
# ЗАПУСК РЕДАКТИРОВАНИЯ КОНКРЕТНОГО ПОЛЯ
# ==========================================
@router.callback_query(F.data.startswith("edit_field_"))
async def start_editing_field(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    user_id = parts[2]
    field_name = parts[3]
    list_type = parts[4]
    page = parts[5]

    if field_name == "programinfo":
        field_name = "program_info"

    if callback.from_user.id != int(user_id) and callback.from_user.id not in ADMINS:
        await callback.answer("⚠️ Доступ запрещен!", show_alert=True)
        return

    await state.update_data(target_user_id=user_id, field_name=field_name, list_type=list_type, page=page)
    await state.set_state(EditSponsorState.waiting_for_new_value)

    field_titles = {
        "age": "новый возраст (цифрой от 18 до 100)",
        "sobriety": "новый срок трезвости",
        "city": "новый город",
        "phone": "новый номер телефона",
        "program_info": "новую информацию об опыте"
    }

    await callback.message.answer(f"✍️ Напишите {field_titles.get(field_name, 'новое значение')} в чат:")
    await callback.answer()

# ==========================================
# СОХРАНЕНИЕ ИЗМЕНЕННОГО ПОЛЯ В БД
# ==========================================
@router.message(EditSponsorState.waiting_for_new_value)
async def save_edited_field(message: Message, state: FSMContext):
    new_value = message.text.strip()
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    field_name = data.get("field_name")

    allowed_fields = ["age", "sobriety", "city", "phone", "program_info"]
    if field_name not in allowed_fields:
        await message.answer("Ошибка поля.")
        await state.clear()
        return

    if field_name == "age":
        if not new_value.isdigit() or not (18 <= int(new_value) <= 100):
            await message.answer("⚠️ Возраст должен состоять только из цифр (от 18 до 100). Попробуйте еще раз:")
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