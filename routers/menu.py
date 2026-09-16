from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import psycopg2
from datetime import datetime
import html
import logging
from routers.reflections import MORNING_PRAYER_TEXT, EVENING_PRAYER_TEXT
from .ai_helper import ask_ai_for_beginner
from config import DATABASE_URL, ADMINS

router = Router()

class EditSponsorState(StatesGroup):
    waiting_for_new_value = State()

class SponsorForm(StatesGroup):
    waiting_for_name = State()

def get_main_menu_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📖 Ежедневные размышления")],
            [types.KeyboardButton(text="🙏 11 Шаг"), types.KeyboardButton(text="➕ Стать спонсором")],
            [types.KeyboardButton(text="🤝 Спонсоры"), types.KeyboardButton(text="📅 Расписание")],
            [types.KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите нужный раздел внизу 👇"
    )

HELP_FOOTER = "\n\nЕсли у вас есть вопросы, нужна поддержка — мы готовы помочь.\n📞 Горячая линия: +7 708 317 17 69"

SCHEDULE_DATA = {
    "s_online": (
        "🌐 <b>ОНЛАЙН</b>\n\n• <b>Пробуждение</b>: Вт, Чт, Сб 21:00\n<a href='https://us06web.zoom.us/j/82036099070'>Zoom</a> | Пароль: +77754565358\n\n"
        "• <b>Бірлік (каз)</b>: Чт 21:00\n<a href='https://us06web.zoom.us/j/7473499478'>Zoom</a> | Пароль: +77074337408\n\n"
        "• <b>Шаг за шагом</b>: Вт 19:00\n<a href='https://t.me/+JqgMpZCz_fY1OTVi'>Telegram</a>" + HELP_FOOTER, []
    ),
    "s_zhub": (
        "🏢 <b>Жубанова 3а</b> (между Алтынсарина и Отеген Батыра)\n301 кабинет, 3 этаж (вход справа от гостиницы \"Достар\")\n\n"
        "• <b>Виктория</b>: Вт, Чт 19:30, Сб 19:00\n• <b>Шапагат (каз)</b>: Пн, Ср 19:00, Сб 17:00\n"
        "• <b>Чайхана (Новички)</b>: Вс 11:00\n• <b>Женский клуб</b>: Вс 13:00" + HELP_FOOTER,
        [InlineKeyboardButton(text="📍 Открыть в 2GIS", url="https://2gis.kz/almaty/geo/9430047375041535/76.857015,43.236908")]
    ),
    "s_zenk": (
        "🏢 <b>Зенкова 24 (Дом Офицеров)</b>\n(вход с ул. Калдаякова, по железной лестнице наверх)\n\n"
        "• <b>8 марта</b>: Ежедневно 19:00, Вт/Чт 12:00\n• <b>АлмА (Женская)</b>: Сб 12:00\n"
        "• <b>ААА (Мужская)</b>: Сб 17:00\n• <b>ВДА</b>: уточнять по контактам" + HELP_FOOTER,
        [InlineKeyboardButton(text="📍 Открыть в 2GIS", url="https://2gis.kz/almaty/geo/70000001112488343")]
    ),
    "s_tim": (
        "🏢 <b>Тимирязева 42, корпус 23, каб 102</b>\n\n"
        "• <b>Друзья Билла</b>: Вт, Чт 12:00\n• <b>Наурыз</b>: Вт, Чт, Пт, Сб 19:00, Вс 15:00" + HELP_FOOTER,
        [InlineKeyboardButton(text="📍 Открыть в 2GIS", url="https://2gis.kz/almaty/geo/9430047374971407/76.904347,43.217837")]
    ),
    "s_other": (
        "📍 <b>Другие локации</b>\n\n• <b>Аксай</b> (Райымбека 493): Вс 13:00\n"
        "• <b>НОВЫЕ ОЧКИ</b> (Жибек Жолы 64): Пн, Ср, Пт 19:00, Сб 14:00\n"
        "• <b>Боралдай</b> (Курчатова 13а): Сб 17:00\n• <b>Талхиз (Талгар)</b> (Муратбаева 26): Пн, Чт, Пт 19:00\n\n"
        "• <b>Турксиб</b>: Уточнять по тел +77478601105\nВремя: Вт, Чт 19:00-20:30; Вс 17:00-18:30" + HELP_FOOTER,
        [
            InlineKeyboardButton(text="📍 Новые Очки (2GIS)", url="https://2gis.kz/almaty/geo/9430047374988153/76.950690,43.262199"),
            InlineKeyboardButton(text="📍 Турксиб (2GIS)", url="https://2gis.kz/almaty/geo/9430047374991567/76.955136,43.330053"),
            InlineKeyboardButton(text="📍 Талхиз (2GIS)", url="https://2gis.kz/almaty/geo/70000001045475756/77.234246,43.317702")
        ]
    )
}

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Приветствую! Добро пожаловать в бот АА.\n\n👇 Выберите нужный раздел:", reply_markup=get_main_menu_keyboard(), parse_mode="HTML")

@router.message(F.text.in_({"🏠 Главное меню", "Главное меню"}))
async def cmd_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 <b>Главное меню</b>", reply_markup=get_main_menu_keyboard(), parse_mode="HTML")

@router.message(F.text == "📖 Ежедневные размышления")
async def show_reflection(message: Message):
    today = datetime.now()
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT text FROM reflections_archive WHERE day = %s AND month = %s", (today.day, today.month))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row and row[0]:
            raw_text = str(row[0])
            lines = [line.strip() for line in raw_text.split('\n') if line and line.strip()]
            filtered = [l for l in lines if "WWW.MOS-NACH.RU" not in l and "Анонимные Алкоголики" not in l]
            body = "\n\n".join(filtered) if filtered else raw_text
            
            safe_text = f"📖 <b>Ежедневные размышления АА</b>\n\n{html.escape(body)}"
            if len(safe_text) > 4000:
                safe_text = safe_text[:4000] + "...\n\n(текст слишком длинный)"

            await message.answer(safe_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
        else:
            await message.answer("На сегодня размышления не найдены.", reply_markup=get_main_menu_keyboard())
    except Exception as e:
        logging.error(f"Reflection error: {e}")
        await message.answer("Произошла ошибка при загрузке размышлений.", reply_markup=get_main_menu_keyboard())

@router.message(F.text == "🙏 11 Шаг")
async def step_eleven(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌅 Утренняя молитва", callback_data="get_morning_prayer")],
        [InlineKeyboardButton(text="🌙 Вечерняя молитва", callback_data="get_evening_prayer")]
    ])
    await message.answer("🙏 <b>11 Шаг программы АА</b>", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.in_({"get_morning_prayer", "get_evening_prayer"}))
async def send_prayer(callback: CallbackQuery):
    text = MORNING_PRAYER_TEXT if callback.data == "get_morning_prayer" else EVENING_PRAYER_TEXT
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@router.message(F.text == "➕ Стать спонсором")
async def become_sponsor(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📝 Заполнить анкету", callback_data="start_sponsor_registration")]])
    await message.answer("➕ <b>Стать спонсором в АА</b>", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "start_sponsor_registration")
async def reg_sponsor(callback: CallbackQuery, state: FSMContext):
    try: await callback.message.delete()
    except: pass
    await callback.message.answer("📝 Введите ваше имя:", parse_mode="HTML")
    await state.set_state(SponsorForm.waiting_for_name)
    await callback.answer()

@router.message(F.text == "🤝 Спонсоры")
@router.callback_query(F.data == "menu_sponsors")
async def sponsors_menu(event: Message | CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👦 Братья", callback_data="list_brothers_0")],
        [InlineKeyboardButton(text="👧 Сестры", callback_data="list_sisters_0")]
    ])
    if isinstance(event, Message):
        await event.answer("👥 Выберите список:", reply_markup=kb)
    else:
        await event.message.edit_text("👥 Выберите список:", reply_markup=kb)
        try: await event.answer()
        except: pass

@router.callback_query(F.data.startswith(("list_brothers_", "list_sisters_")))
async def show_list_page(callback: CallbackQuery):
    _, list_type, page_str = callback.data.split("_")
    page = int(page_str)
    label, db_kw = ("Братья", "брат") if list_type == "brothers" else ("Сестры", "сестр")
    gender_fl = "OR gender ILIKE '%муж%'" if list_type == "brothers" else "OR gender ILIKE '%жен%'"

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(f"SELECT user_id, name, age, city, sobriety FROM sponsors WHERE gender ILIKE '%{db_kw}%' {gender_fl};")
    sponsors = cur.fetchall()
    cur.close()
    conn.close()

    if not sponsors:
        return await callback.answer(f"Список {label} пуст.", show_alert=True)

    PER_PAGE = 5
    total_pages = (len(sponsors) + PER_PAGE - 1) // PER_PAGE
    current = sponsors[page * PER_PAGE : (page + 1) * PER_PAGE]

    kb = [[InlineKeyboardButton(text=f"{n}, {a} лет | {c or 'Город'} | {s}", callback_data=f"view_sp_{uid}_{list_type}_{page}")] for uid, n, a, c, s in current]
    
    nav = []
    if page > 0: nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"list_{list_type}_{page - 1}"))
    if (page + 1) * PER_PAGE < len(sponsors): nav.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"list_{list_type}_{page + 1}"))
    if nav: kb.append(nav)
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_sponsors")])

    await callback.message.edit_text(f"📖 Список ({label}) — Страница {page + 1} из {total_pages}:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@router.callback_query(F.data.startswith("view_sp_"))
async def show_details(callback: CallbackQuery):
    _, _, user_id, list_type, page = callback.data.split("_")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT name, gender, age, sobriety, city, username, phone, program_info FROM sponsors WHERE user_id = %s;", (user_id,))
    sp = cur.fetchone()
    cur.close()
    conn.close()

    if not sp:
        return await callback.answer("⚠️ Спонсор не найден.", show_alert=True)

    name, gender, age, sobriety, city, username, phone, prog = sp
    tg = f"@{username}" if username and username not in ("-", "нет") else f"ID: {user_id}"
    text = f"👤 Спонсор: {name} ({gender}), {age} лет\n🕊 Трезвость: {sobriety}\n📍 Город: {city}\n📖 Опыт: {prog}\n✈️ Telegram: {tg}\n📞 Телефон: {phone}"
    
    kb = [[InlineKeyboardButton(text="⬅️ Назад", callback_data=f"list_{list_type}_{page}")]]
    if callback.from_user.id == int(user_id) or callback.from_user.id in ADMINS:
        kb.insert(0, [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_menu_{user_id}_{list_type}_{page}")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@router.callback_query(F.data.startswith("edit_menu_"))
async def edit_menu(callback: CallbackQuery):
    _, _, user_id, list_type, page = callback.data.split("_")
    if callback.from_user.id != int(user_id) and callback.from_user.id not in ADMINS:
        return await callback.answer("⚠️ Доступ запрещен!", show_alert=True)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Возраст", callback_data=f"edit_field_{user_id}_age_{list_type}_{page}")],
        [InlineKeyboardButton(text="🕊 Срок трезвости", callback_data=f"edit_field_{user_id}_sobriety_{list_type}_{page}")],
        [InlineKeyboardButton(text="📍 Город", callback_data=f"edit_field_{user_id}_city_{list_type}_{page}")],
        [InlineKeyboardButton(text="📞 Телефон", callback_data=f"edit_field_{user_id}_phone_{list_type}_{page}")],
        [InlineKeyboardButton(text="📖 Опыт", callback_data=f"edit_field_{user_id}_program_info_{list_type}_{page}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"view_sp_{user_id}_{list_type}_{page}")]
    ])
    await callback.message.edit_text("⚙️ Выберите поле для изменения:", reply_markup=kb)

@router.callback_query(F.data.startswith("edit_field_"))
async def edit_field(callback: CallbackQuery, state: FSMContext):
    _, _, user_id, field, list_type, page = callback.data.split("_")
    if callback.from_user.id != int(user_id) and callback.from_user.id not in ADMINS:
        return await callback.answer("⚠️ Доступ запрещен!", show_alert=True)

    await state.update_data(target_user_id=user_id, field_name=field, list_type=list_type, page=page)
    await state.set_state(EditSponsorState.waiting_for_new_value)
    await callback.message.answer("✍️ Напишите новое значение в чат:")
    await callback.answer()

@router.message(EditSponsorState.waiting_for_new_value)
async def save_field(message: Message, state: FSMContext):
    val, data = message.text.strip(), await state.get_data()
    uid, field = data.get("target_user_id"), data.get("field_name")
    
    if field == "age" and (not val.isdigit() or not (18 <= int(val) <= 100)):
        return await message.answer("⚠️ Возраст должен быть числом от 18 до 100:")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(f"UPDATE sponsors SET {field} = %s WHERE user_id = %s;", (val, uid))
        conn.commit()
        cur.close()
        conn.close()
        await message.answer("✅ Данные обновлены!")
    except Exception as e:
        logging.error(f"DB update error: {e}")
        await message.answer("❌ Ошибка сохранения.")
    await state.clear()

def get_schedule_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Онлайн группы", callback_data="s_online")],
        [InlineKeyboardButton(text="📍 Алматы: Жубанова 3а", callback_data="s_zhub")],
        [InlineKeyboardButton(text="📍 Алматы: Зенкова 24", callback_data="s_zenk")],
        [InlineKeyboardButton(text="📍 Алматы: Тимирязева 42", callback_data="s_tim")],
        [InlineKeyboardButton(text="📍 Другие локации", callback_data="s_other")]
    ])

@router.message(F.text == "📅 Расписание")
async def show_schedule(message: Message):
    await message.answer("📅 <b>Расписание собраний АА</b>\nВыберите локацию:", reply_markup=get_schedule_kb(), parse_mode="HTML")

@router.callback_query(F.data.startswith("s_"))
async def callback_schedule(callback: CallbackQuery):
    if callback.data == "s_back":
        return await callback.message.edit_text("📅 <b>Расписание собраний АА</b>\nВыберите локацию:", reply_markup=get_schedule_kb(), parse_mode="HTML")
    
    if callback.data in SCHEDULE_DATA:
        text, extra_buttons = SCHEDULE_DATA[callback.data]
        kb = [[btn] for btn in extra_buttons] + [[InlineKeyboardButton(text="⬅️ Назад", callback_data="s_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()

@router.message(F.text == "❓ Помощь")
async def help_handler(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="👤 Позвать живого служащего", callback_data="call_servant")]])
    await message.answer("❓ <b>Помощь и поддержка</b>", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "back_to_menu")
async def back_menu(callback: CallbackQuery):
    try: await callback.message.delete()
    except: pass
    await callback.message.answer("🏠 <b>Главное меню</b>", reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "call_servant")
async def call_servant(callback: CallbackQuery):
    await callback.message.answer("🙏 Ваша заявка принята. Дежурный служащий свяжется с вами.")
    await callback.answer()

@router.message(StateFilter(None), F.text)
async def ai_handler(message: Message, state: FSMContext):
    if message.text in {"📖 Ежедневные размышления", "🙏 11 Шаг", "➕ Стать спонсором", "🤝 Спонсоры", "📅 Расписание", "❓ Помощь", "🏠 Главное меню", "Главное меню"}:
        return
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    response = await ask_ai_for_beginner(message.from_user.id, message.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="👤 Позвать живого служащего", callback_data="call_servant")]])
    await message.answer(response, parse_mode="Markdown", reply_markup=kb)