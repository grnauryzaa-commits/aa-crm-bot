from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
import psycopg2
from datetime import datetime
import html
import logging
from routers.reflections import MORNING_PRAYER_TEXT, EVENING_PRAYER_TEXT
from .ai_helper import ask_ai_for_beginner
from config import DATABASE_URL, SERVANT_CHAT_IDS

router = Router()

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

def format_reflection_text(text, today):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    forbidden = [
        "WWW.MOS-NACH.RU", "Анонимные Алкоголики.", "Группа", "Поделиться:", 
        "Рассказать:", "Twitter", "Facebook", "Vkontakte", "WhatsApp", 
        "Telegram", "EMail", "Тег audio", "Aудио-ежедневник", 
        "Skype", "Mail", "Альтернативный вариант",
        "Ежедневные Размышления на", "Сегодня"
    ]
    filtered = [line for line in lines if not any(f in line for f in forbidden)]
    if len(filtered) > 0 and f"{today.day}" in filtered[0] and "июня" in filtered[0].lower() and len(filtered[0]) < 20:
        filtered.pop(0)
    
    body = "\n\n".join(filtered)
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", 
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    return f"📖 <b>Ежедневные размышления АА</b>\n\n📋 <b>{today.day} {months[today.month - 1]}</b>\n\n{html.escape(body)}"

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Приветствую! Добро пожаловать в бот сообщества Анонимных Алкоголиков.\n\n"
        "🤖 Вы можете задать мне любой вопрос о программе АА своими словами, и я постараюсь помочь.\n\n"
        "👇 <b>Главное меню всегда находится внизу экрана.</b> Нажимайте на нужные кнопки:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text.in_({"🏠 Главное меню", "Главное меню"}))
async def cmd_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 <b>Главное меню</b>\n\nВыберите нужный раздел внизу 👇",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "📖 Ежедневные размышления")
async def show_daily_reflection(message: types.Message):
    today = datetime.now()
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT text FROM reflections_archive WHERE day = %s AND month = %s", (today.day, today.month))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            text = format_reflection_text(row[0], today)
            await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
        else:
            await message.answer("На сегодня размышления не найдены в базе.", reply_markup=get_main_menu_keyboard())
    except Exception as e:
        logging.error(f"Ошибка получения размышлений: {e}")
        await message.answer("Произошла ошибка при получении размышлений.", reply_markup=get_main_menu_keyboard())

@router.message(F.text == "🙏 11 Шаг")
async def step_eleven_menu(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌅 Утренняя молитва", callback_data="get_morning_prayer")],
            [InlineKeyboardButton(text="🌙 Вечерняя молитва", callback_data="get_evening_prayer")]
        ]
    )
    await message.answer(
        "🙏 <b>11 Шаг программы АА</b>\n\nВыберите нужную практику:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "get_morning_prayer")
async def send_morning_callback(callback: types.CallbackQuery):
    await callback.message.answer(MORNING_PRAYER_TEXT, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "get_evening_prayer")
async def send_evening_callback(callback: types.CallbackQuery):
    await callback.message.answer(EVENING_PRAYER_TEXT, parse_mode="HTML")
    await callback.answer()

@router.message(F.text == "➕ Стать спонсором")
async def become_sponsors_menu(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Заполнить анкету спонсора", callback_data="start_sponsor_registration")],
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
        ]
    )
    await message.answer(
        "➕ <b>Стать спонсором в АА</b>\n\n"
        "Спонсор — это человек, который прошел Шаги и готов делиться опытом с другими.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.message(F.text == "🤝 Спонсоры")
@router.callback_query(F.data == "menu_sponsors")
async def sponsors_menu_handler(event: Message | CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👦 Братья", callback_data="list_brothers_0")],
        [InlineKeyboardButton(text="👧 Сестры", callback_data="list_sisters_0")]
    ])
    if isinstance(event, Message):
        await event.answer("👥 Выберите список:", reply_markup=keyboard)
    else:
        await event.message.edit_text("👥 Выберите список:", reply_markup=keyboard)
        await event.answer()

def get_schedule_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Онлайн группы", callback_data="s_online")],
        [InlineKeyboardButton(text="📍 Алматы: Жубанова 3а", callback_data="s_zhub")],
        [InlineKeyboardButton(text="📍 Алматы: Зенкова 24", callback_data="s_zenk")],
        [InlineKeyboardButton(text="📍 Алматы: Тимирязева 42", callback_data="s_tim")],
        [InlineKeyboardButton(text="📍 Каскелен: Нур-Жанат", callback_data="s_kaskelen")],
        [InlineKeyboardButton(text="📍 Другие локации", callback_data="s_other")]
    ])

@router.message(F.text == "📅 Расписание")
async def show_schedule_menu(message: types.Message):
    await message.answer("📅 <b>Расписание собраний АА</b>\nВыберите локацию:", reply_markup=get_schedule_menu_kb(), parse_mode="HTML")

@router.callback_query(F.data.startswith("s_"))
async def callback_schedule(callback: types.CallbackQuery):
    data = callback.data
    kb_back = [[InlineKeyboardButton(text="⬅️ Назад", callback_data="s_back")]]
    
    help_text = "\n\nЕсли у вас есть вопросы, нужна поддержка — мы готовы помочь.\n📞 Горячая линия: +7 708 317 17 69"

    if data == "s_back":
        await callback.message.edit_text("📅 <b>Расписание собраний АА</b>\nВыберите локацию:", reply_markup=get_schedule_menu_kb(), parse_mode="HTML")
    
    elif data == "s_online":
        text = ("🌐 <b>ОНЛАЙН</b>\n\n• <b>Пробуждение</b>: Вт, Чт, Сб 21:00\n<a href='https://us06web.zoom.us/j/82036099070'>Zoom</a> | Пароль: +77754565358\n\n"
                "• <b>Бірлік (каз)</b>: Чт 21:00\n<a href='https://us06web.zoom.us/j/7473499478'>Zoom</a> | Пароль: +77074337408\n\n"
                "• <b>Шаг за шагом</b>: Вт 19:00\n<a href='https://t.me/+JqgMpZCz_fY1OTVi'>Telegram</a>" + help_text)
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_back), parse_mode="HTML", disable_web_page_preview=True)

    elif data == "s_zhub":
        text = ("🏢 <b>Жубанова 3а</b> (между Алтынсарина и Отеген Батыра)\n301 кабинет, 3 этаж (вход справа от гостиницы \"Достар\")\n\n"
                "• <b>Виктория</b>: Вт, Чт 19:30, Сб 19:00\n• <b>Шапагат (каз)</b>: Пн, Ср 19:00, Сб 17:00\n"
                "• <b>Чайхана (Новички)</b>: Вс 11:00\n• <b>Женский клуб</b>: Вс 13:00" + help_text)
        kb = [[InlineKeyboardButton(text="📍 Открыть в 2GIS", url="https://2gis.kz/almaty/geo/9430047375041535/76.857015,43.236908")],
              [InlineKeyboardButton(text="⬅️ Назад", callback_data="s_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

    elif data == "s_zenk":
        text = ("🏢 <b>Зенкова 24 (Дом Офицеров)</b>\n(вход с ул. Калдаякова, по железной лестнице наверх)\n\n"
                "• <b>8 марта</b>: Ежедневно 19:00, Вт/Чт 12:00\n• <b>АлмА (Женская)</b>: Сб 12:00\n"
                "• <b>ААА (Мужская)</b>: Сб 17:00\n• <b>ВДА</b>: уточнять по контактам" + help_text)
        kb = [[InlineKeyboardButton(text="📍 Открыть в 2GIS", url="https://2gis.kz/almaty/geo/70000001112488343")],
              [InlineKeyboardButton(text="⬅️ Назад", callback_data="s_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

    elif data == "s_tim":
        text = ("🏢 <b>Тимирязева 42, корпус 23, каб 102</b>\n\n"
                "• <b>Друзья Билла</b>: Вт, Чт 12:00\n• <b>Наурыз</b>: Вт, Чт, Пт, Сб 19:00, Вс 15:00" + help_text)
        kb = [[InlineKeyboardButton(text="📍 Открыть в 2GIS", url="https://2gis.kz/almaty/geo/9430047374971407/76.904347,43.217837")],
              [InlineKeyboardButton(text="⬅️ Назад", callback_data="s_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

    elif data == "s_kaskelen":
        text = ("🏢 <b>ТД «Нур-Жанат» (г. Каскелен)</b>\n\n"
                "• <b>Группа «Туран»</b>: Пн, Ср, Сб 17:00–18:15" + help_text)
        kb = [[InlineKeyboardButton(text="📍 Открыть в 2GIS", url="https://2gis.kz/almaty/geo/70030076201734271/76.642795,43.201247")],
              [InlineKeyboardButton(text="⬅️ Назад", callback_data="s_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

    elif data == "s_other":
        text = ("📍 <b>Другие локации</b>\n\n• <b>Аксай</b> (Райымбека 493): Вс 13:00\n"
                "• <b>НОВЫЕ ОЧКИ</b> (Жибек Жолы 64): Пн, Ср, Пт 19:00, Сб 14:00\n"
                "• <b>Боралдай</b> (Курчатова 13а): Сб 17:00\n• <b>Талхиз (Талгар)</b> (Муратбаева 26): Пн, Чт, Пт 19:00\n\n"
                "• <b>Турксиб</b>: Уточнять по тел +77478601105\nВремя: Вт, Чт 19:00-20:30; Вс 17:00-18:30" + help_text)
        kb = [[InlineKeyboardButton(text="📍 Новые Очки (2GIS)", url="https://2gis.kz/almaty/geo/9430047374988153/76.950690,43.262199")],
              [InlineKeyboardButton(text="📍 Турксиб (2GIS)", url="https://2gis.kz/almaty/geo/9430047374991567/76.955136,43.330053")],
              [InlineKeyboardButton(text="📍 Талхиз (2GIS)", url="https://2gis.kz/almaty/geo/70000001045475756/77.234246,43.317702")],
              [InlineKeyboardButton(text="⬅️ Назад", callback_data="s_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")
    
    await callback.answer()

@router.message(F.text == "❓ Помощь")
async def help_section_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Позвать живого служащего", callback_data="call_servant")]
        ]
    )
    await message.answer(
        "❓ <b>Помощь и поддержка</b>\n\n"
        "Если вам тяжело или у вас срочный вопрос — вы можете задать мне в чате или позвать дежурного служащего.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(
        "🏠 <b>Главное меню</b>",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer("Возврат в меню")

@router.callback_query(F.data == "call_servant")
async def call_servant_callback(callback: types.CallbackQuery):
    user = callback.from_user
    user_link = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"
    username_text = f" (@{user.username})" if user.username else ""
    
    alert_text = (
        f"🚨 <b>Новый запрос о помощи!</b>\n\n"
        f"Пользователь: {user_link}{username_text}\n"
        f"ID: <code>{user.id}</code>\n"
        f"Нажал кнопку «Позвать живого служащего»."
    )

    for servant_id in SERVANT_CHAT_IDS:
        try:
            await callback.bot.send_message(
                chat_id=servant_id,
                text=alert_text,
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление служащему {servant_id}: {e}")

    await callback.message.answer(
        "🙏 Ваша заявка принята. Дежурный служащий сообщества уведомлен и свяжется с вами в ближайшее время."
    )
    await callback.answer()

@router.message(StateFilter(None), F.text)
async def handle_beginner_questions(message: types.Message, state: FSMContext):
    # ЗАЩИТА: Бот отвечает ИИ-сообщениями ТОЛЬКО в личных чатах (ЛС). 
    # В любых группах, супергруппах и каналах (включая чат Наурыз) он полностью молчит.
    if message.chat.type != "private":
        return

    menu_buttons = [
        "📖 Ежедневные размышления", "🙏 11 Шаг", 
        "➕ Стать спонсором", "🤝 Спонсоры", 
        "📅 Расписание", "❓ Помощь", "🏠 Главное меню", "Главное меню"
    ]
    if message.text in menu_buttons:
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    ai_response = await ask_ai_for_beginner(message.from_user.id, message.text)
    
    servant_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Позвать живого служащего", callback_data="call_servant")]
        ]
    )
    await message.answer(ai_response, parse_mode="Markdown", reply_markup=servant_keyboard)