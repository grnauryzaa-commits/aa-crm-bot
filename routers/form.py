from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from routers.states import SponsorForm
from routers.menu import get_main_menu_keyboard
from config import ADMINS, DATABASE_URL
import database as db
import psycopg2
import html

router = Router()

# ==========================================
# ШАГИ РЕГИСТРАЦИИ СПОНСОРА ЧЕРЕЗ FSM
# ==========================================

@router.message(F.text == "➕ Стать спонсором")
async def start_form(message: Message, state: FSMContext):
    await message.answer("👤 Напиши свое имя:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SponsorForm.name)

@router.message(SponsorForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Какой твой пол? (Брат / Сестра)")
    await state.set_state(SponsorForm.gender)

@router.message(SponsorForm.gender)
async def process_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer("📅 Напиши свой возраст (цифрой):")
    await state.set_state(SponsorForm.age)

@router.message(SponsorForm.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("🕊 Какой у тебя срок трезвости? (например: 3 года 2 месяца)")
    await state.set_state(SponsorForm.sobriety)

@router.message(SponsorForm.sobriety)
async def process_sobriety(message: Message, state: FSMContext):
    await state.update_data(sobriety=message.text)
    await message.answer("📍 Из какого ты города?")
    await state.set_state(SponsorForm.city)

@router.message(SponsorForm.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("📖 Напиши коротко о своем опыте по программе / спонсорстве:")
    await state.set_state(SponsorForm.program_info)

@router.message(SponsorForm.program_info)
async def process_program_info(message: Message, state: FSMContext):
    await state.update_data(program_info=message.text)
    await message.answer("📞 Напиши свой номер телефона для связи:")
    await state.set_state(SponsorForm.phone)

@router.message(SponsorForm.phone)
async def process_phone(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    tg_id = message.from_user.id
    
    sponsor_data = {
        'name': data.get('name'),
        'gender': data.get('gender'),
        'age': data.get('age'),
        'sobriety': data.get('sobriety'),
        'city': data.get('city'),
        'program_info': data.get('program_info'),
        'username': message.from_user.username or "нет",
        'phone': data.get('phone')
    }

    try:
        await db.save_sponsor_draft(tg_id, sponsor_data)
    except Exception as e:
        print(f"Ошибка сохранения черновика в БД: {e}")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить карточку", callback_data=f"approve_sp_{tg_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_sp_{tg_id}")
        ]
    ])
    
    admin_text = (
        "🔔 ЗАЯВКА НА РЕГИСТРАЦИЮ СПОНСОРА\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 Имя: {html.escape(str(sponsor_data['name']))} ({html.escape(str(sponsor_data['gender']))})\n"
        f"📅 Возраст: {html.escape(str(sponsor_data['age']))}\n"
        f"🕊 Трезвость: {html.escape(str(sponsor_data['sobriety']))}\n"
        f"📍 Город: {html.escape(str(sponsor_data['city']))}\n\n"
        f"📖 Опыт/Программа: {html.escape(str(sponsor_data['program_info']))}\n"
        f"✈️ Telegram: @{html.escape(str(sponsor_data['username']))}\n"
        f"📞 Телефон: {html.escape(str(sponsor_data['phone']))}\n"
        "━━━━━━━━━━━━━━━━━━"
    )

    for admin_id in ADMINS:
        try:
            await bot.send_message(chat_id=admin_id, text=admin_text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            print(f"Не удалось отправить админу {admin_id}: {e}")
    
    await message.answer("✅ Твоя анкета успешно отправлена на модерацию администратору!", reply_markup=get_main_menu_keyboard())
    await state.clear()


# ==========================================
# МОДЕРАЦИЯ АНКЕТ АДМИНИСТРАТОРАМИ (ОДОБРИТЬ / ОТКЛОНИТЬ)
# ==========================================

@router.callback_query(F.data.startswith("approve_sp_"))
async def approve_sponsor(callback: CallbackQuery, bot: Bot):
    target_user_id = int(callback.data.split("_")[2])
    print(f"DEBUG: Нажата кнопка ОДОБРИТЬ для пользователя {target_user_id}")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("SELECT name, gender, age, sobriety, city, username, phone, program_info FROM sponsor_drafts WHERE user_id = %s;", (target_user_id,))
        draft = cur.fetchone()
        
        if draft:
            cur.execute("""
                INSERT INTO sponsors (user_id, name, gender, age, sobriety, city, username, phone, program_info)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    name = EXCLUDED.name, gender = EXCLUDED.gender, age = EXCLUDED.age,
                    sobriety = EXCLUDED.sobriety, city = EXCLUDED.city, username = EXCLUDED.username,
                    phone = EXCLUDED.phone, program_info = EXCLUDED.program_info;
            """, (target_user_id, *draft))
            
            cur.execute("DELETE FROM sponsor_drafts WHERE user_id = %s;", (target_user_id,))
            conn.commit()
            
        cur.close()
        conn.close()

        await callback.message.edit_text(f"{callback.message.text}\n\n✅ ОДОБРЕНО АДМИНИСТРАТОРОМ", reply_markup=None)
        await callback.answer("Анкета одобрена!")
        
        try:
            await bot.send_message(target_user_id, "🎉 Поздравляем! Ваша анкета спонсора одобрена.")
        except:
            pass
            
    except Exception as e:
        print(f"Ошибка в approve: {e}")
        await callback.answer("Ошибка БД", show_alert=True)

@router.callback_query(F.data.startswith("decline_sp_"))
async def decline_sponsor(callback: CallbackQuery, bot: Bot):
    target_user_id = int(callback.data.split("_")[2])
    print(f"DEBUG: Нажата кнопка ОТКЛОНИТЬ для пользователя {target_user_id}")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("DELETE FROM sponsor_drafts WHERE user_id = %s;", (target_user_id,))
        conn.commit()
        cur.close()
        conn.close()

        await callback.message.edit_text(f"{callback.message.text}\n\n❌ ОТКЛОНЕНО АДМИНИСТРАТОРОМ", reply_markup=None)
        await callback.answer("Анкета отклонена.")
        
        try:
            await bot.send_message(target_user_id, "❌ К сожалению, ваша анкета спонсора была отклонена.")
        except:
            pass
    except Exception as e:
        print(f"Ошибка в decline: {e}")
        await callback.answer("Ошибка БД", show_alert=True)


# ==========================================
# ПРОСМОТР СПИСКА СПОНСОРОВ И ИХ ДЕТАЛЕЙ
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
    else:
        await callback.answer("⚠️ Спонсор не найден в базе данных.", show_alert=True)

@router.callback_query(F.data.startswith("list_"))
async def handle_list_navigation(callback: CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) == 3 and parts[1] in ["brothers", "sisters"]:
        await show_list_page(callback)