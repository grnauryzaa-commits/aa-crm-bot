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
from database import get_user_language, set_user_language

router = Router()

TEXTS = {
    "ru": {
        "start": "Приветствую! Добро пожаловать в бот сообщества Анонимных Алкоголиков.\n\n🤖 Вы можете задать мне любой вопрос о программе АА своими словами, и я постараюсь помочь.\n\n👇 <b>Главное меню всегда находится внизу экрана.</b>",
        "menu": "🏠 <b>Главное меню</b>\n\nВыберите нужный раздел внизу 👇",
        "choose_lang": "🌐 Выберите язык интерфейса и общения с ботом:",
        "lang_changed": "✅ Язык успешно изменен на русский!",
        "reflection_err": "На сегодня размышления не найдены в базе.",
        "reflection_err_load": "Произошла ошибка при получении размышлений.",
        "btns": ["📖 Ежедневные размышления", "🙏 11 Шаг", "➕ Стать спонсором", "🤝 Спонсоры", "📅 Расписание", "❓ Помощь", "🌐 Язык: Русский"],
        "step11_title": "🙏 <b>11 Шаг программы АА</b>\n\nВыберите нужную практику:",
        "sponsor_title": "➕ <b>Стать спонсором в АА</b>\n\nСпонсор — это человек, который прошел Шаги и готов делиться опытом с другими.",
        "sponsors_title": "👥 Выберите список:",
        "schedule_title": "📅 <b>Расписание собраний АА</b>\nВыберите локацию:",
        "help_title": "❓ <b>Помощь и поддержка</b>\n\nЕсли вам тяжело или у вас срочный вопрос — вы можете задать его мне в чате или позвать дежурного служащего.",
        "servant_alert": "🚨 <b>Новый запрос о помощи!</b>\n\nПользователь: {user_link}{username}\nID: <code>{user.id}</code>\nНажал кнопку «Позвать живого служащего».",
        "servant_success": "🙏 Ваша заявка принята. Дежурный служащий сообщества уведомлен и свяжется с вами в ближайшее время.",
        "help_line": "\n\nЕсли у вас есть вопросы, нужна поддержка — мы готовы помочь.\n📞 Горячая линия: +7 708 317 17 69"
    },
    "kk": {
        "start": "Қош келдіңіз! Анонимді Алкоголиктер қауымдастығының ботына қош келдіңіз.\n\n🤖 Сіз маған АА бағдарламасы туралой кез келген сұрақты өз сөзіңізбен қоя аласыз, мен көмектесуге тырысамын.\n\n👇 <b>Басты мәзір әрқашан экранның төменгі бөлігінде орналасқан.</b>",
        "menu": "🏠 <b>Басты мәзір</b>\n\nТөменден қажетті бөлімді таңдаңыз 👇",
        "choose_lang": "🌐 Тілді таңдаңыз / Выберите язык:",
        "lang_changed": "✅ Тіл қазақ тіліне өзгертілді!",
        "reflection_err": "Бүгінге ой-толғаулар табылмады.",
        "reflection_err_load": "Ой-толғауларды алу кезінде қате орын алды.",
        "btns": ["📖 Күнделікті ой-толғаулар", "🙏 11 Қадам", "➕ Демеуші болу", "🤝 Демеушілер", "📅 Кесте", "❓ Көмек", "🌐 Тіл: Қазақша"],
        "step11_title": "🙏 <b>АА 11-ші қадамы</b>\n\nҚажетті тәжірибені таңдаңыз:",
        "sponsor_title": "➕ <b>АА-да демеуші болу</b>\n\nДемеуші — бұл Қадамдардан өткен және басқалармен тәжірибе бөлісуге дайын адам.",
        "sponsors_title": "👥 Тізімді таңдаңыз:",
        "schedule_title": "📅 <b>АА жиналыстарының кестесі</b>\nОрынды таңдаңыз:",
        "help_title": "❓ <b>Көмек және қолдау</b>\n\nЕгер сізге қиын болса немесе шұғыл сұрағыңыз болса — оны маған чатта қоюға немесе кезекші қызметкерді шақыруға болады.",
        "servant_alert": "🚨 <b>Жаңа көмек сұрау!</b>\n\nПайдаланушы: {user_link}{username}\nID: <code>{user.id}</code>\n«Тірі қызметкерді шақыру» түймесін басты.",
        "servant_success": "🙏 Өтінішіңіз қабылданды. Қауымдастықтың кезекші қызметкері хабардар етілді және жақын арада сізбен байланысады.",
        "help_line": "\n\nЕгер сізде сұрақтар туындаса, қолдау қажет болса — біз көмектесуге дайынбыз.\n📞 Жедел желі: +7 708 317 17 69"
    }
}

SCHEDULE_DATA = {
    "s_online": "🌐 <b>ОНЛАЙН</b>\n\n• <b>Пробуждение</b>: Вт, Чт, Сб 21:00\n<a href='https://us06web.zoom.us/j/82036099070'>Zoom</a> | Пароль: +77754565358\n\n• <b>Бірлік (каз)</b>: Чт 21:00\n<a href='https://us06web.zoom.us/j/7473499478'>Zoom</a> | Пароль: +77074337408\n\n• <b>Шаг за шагом</b>: Вт 19:00\n<a href='https://t.me/+JqgMpZCz_fY1OTVi'>Telegram</a>",
    "s_zhub": "🏢 <b>Жубанова 3а</b> (между Алтынсарина и Отеген Батыра)\n301 кабинет, 3 этаж\n\n• <b>Виктория</b>: Вт, Чт 19:30, Сб 19:00\n• <b>Шапагат (каз)</b>: Пн, Ср 19:00, Сб 17:00\n• <b>Чайхана (Новички)</b>: Вс 11:00\n• <b>Женский клуб</b>: Вс 13:00",
    "s_zenk": "🏢 <b>Зенкова 24 (Дом Офицеров)</b>\n(вход с ул. Калдаякова)\n\n• <b>8 марта</b>: Ежедневно 19:00, Вт/Чт 12:00\n• <b>АлмА (Женская)</b>: Сб 12:00\n• <b>ААА (Мужская)</b>: Сб 17:00",
    "s_tim": "🏢 <b>Тимирязева 42, корпус 23, каб 102</b>\n\n• <b>Друзья Билла</b>: Вт, Чт 12:00\n• <b>Наурыз</b>: Вт, Чт, Пт, Сб 19:00, Вс 15:00",
    "s_kaskelen": "🏢 <b>ТД «Нур-Жанат» (г. Каскелен)</b>\n\n• <b>Группа «Туран»</b>: Пн, Ср, Сб 17:00–18:15",
    "s_other": "📍 <b>Другие локации</b>\n\n• <b>Аксай</b> (Райымбека 493): Вс 13:00\n• <b>НОВЫЕ ОЧКИ</b> (Жибек Жолы 64): Пн, Ср, Пт 19:00, Сб 14:00\n• <b>Боралдай</b> (Курчатова 13а): Сб 17:00\n• <b>Талхиз (Талгар)</b>: Пн, Чт, Пт 19:00\n• <b>Турксиб</b>: +77478601105 (Вт, Чт 19:00; Вс 17:00)"
}

SCHEDULE_URLS = {
    "s_zhub": "https://2gis.kz/almaty/geo/9430047375041535/76.857015,43.236908",
    "s_zenk": "https://2gis.kz/almaty/geo/70000001112488343",
    "s_tim": "https://2gis.kz/almaty/geo/9430047374971407/76.904347,43.217837",
    "s_kaskelen": "https://2gis.kz/almaty/geo/70030076201734271/76.642795,43.201247"
}

def get_menu_kb(lang='ru'):
    b = TEXTS[lang]["btns"]
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=b[0])],
            [types.KeyboardButton(text=b[1]), types.KeyboardButton(text=b[2])],
            [types.KeyboardButton(text=b[3]), types.KeyboardButton(text=b[4])],
            [types.KeyboardButton(text=b[5]), types.KeyboardButton(text=b[6])]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел / Бөлімді таңдаңыз 👇"
    )

def get_schedule_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Онлайн группы", callback_data="s_online")],
        [InlineKeyboardButton(text="📍 Алматы: Жубанова 3а", callback_data="s_zhub")],
        [InlineKeyboardButton(text="📍 Алматы: Зенкова 24", callback_data="s_zenk")],
        [InlineKeyboardButton(text="📍 Алматы: Тимирязева 42", callback_data="s_tim")],
        [InlineKeyboardButton(text="📍 Каскелен: Нур-Жанат", callback_data="s_kaskelen")],
        [InlineKeyboardButton(text="📍 Другие локации", callback_data="s_other")]
    ])

def format_reflection(text, today):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    forbidden = ["WWW.MOS-NACH.RU", "Анонимные Алкоголики.", "Группа", "Поделиться:", "Рассказать:", "Twitter", "Facebook", "Vkontakte", "WhatsApp", "Telegram", "EMail", "Тег audio", "Aудио-ежедневник", "Skype", "Mail", "Альтернативный вариант", "Ежедневные Размышления на", "Сегодня"]
    filtered = [l for l in lines if not any(f.casefold() in l.casefold() for f in forbidden)]
    for _ in range(2):
        if filtered and f"{today.day}" in filtered[0] and len(filtered[0]) < 25:
            filtered.pop(0)
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    return f"📖 <b>Ежедневные размышления АА</b>\n\n📋 <b>{today.day} {months[today.month - 1]}</b>\n\n{html.escape('\n\n'.join(filtered))}"

@router.message(Command("start"))
@router.message(F.text.in_({"🏠 Главное меню", "Главное меню", "🏠 Басты мәзір", "Басты мәзір"}))
async def cmd_start_menu(message: types.Message, state: FSMContext):
    await state.clear()
    lang = await get_user_language(message.from_user.id)
    text = TEXTS[lang]["start"] if message.text and message.text.startswith("/") else TEXTS[lang]["menu"]
    await message.answer(text, reply_markup=get_menu_kb(lang), parse_mode="HTML")

@router.message(F.text.in_({"🌐 Язык: Русский", "🌐 Тіл: Қазақша"}))
async def language_menu(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru")],
        [InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="set_lang_kk")]
    ])
    await message.answer(TEXTS[lang]["choose_lang"], reply_markup=kb)

@router.callback_query(F.data.startswith("set_lang_"))
async def set_lang(callback: CallbackQuery):
    lang = callback.data.split("_")[2]
    await set_user_language(callback.from_user.id, lang)
    await callback.message.answer(TEXTS[lang]["lang_changed"], reply_markup=get_menu_kb(lang))
    await callback.answer()

@router.message(F.text.in_({"📖 Ежедневные размышления", "📖 Күнделікті ой-толғаулар"}))
async def show_reflection(message: types.Message):
    today = datetime.now()
    lang = await get_user_language(message.from_user.id)
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT text FROM reflections_archive WHERE day = %s AND month = %s", (today.day, today.month))
        row = cur.fetchone()
        cur.close()
        conn.close()
        text = format_reflection(row[0], today) if row else TEXTS[lang]["reflection_err"]
        await message.answer(text, parse_mode="HTML", reply_markup=get_menu_kb(lang))
    except Exception as e:
        logging.error(f"Ошибка размышлений: {e}")
        await message.answer(TEXTS[lang]["reflection_err_load"], reply_markup=get_menu_kb(lang))

@router.message(F.text.in_({"🙏 11 Шаг", "🙏 11 Қадам"}))
async def step_eleven(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌅 Утренняя молитва / Таңертеңгі дұға", callback_data="get_morning_prayer")],
        [InlineKeyboardButton(text="🌙 Вечерняя молитва / Кешкі дұға", callback_data="get_evening_prayer")]
    ])
    await message.answer(TEXTS[lang]["step11_title"], reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.in_({"get_morning_prayer", "get_evening_prayer"}))
async def send_prayer(callback: CallbackQuery):
    text = MORNING_PRAYER_TEXT if callback.data == "get_morning_prayer" else EVENING_PRAYER_TEXT
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@router.message(F.text.in_({"➕ Стать спонсором", "➕ Демеуші болу"}))
async def sponsor_menu(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Заполнить анкету / Сауалнама", callback_data="start_sponsor_registration")],
        [InlineKeyboardButton(text="🔙 Назад / Мәзірге", callback_data="back_to_menu")]
    ])
    await message.answer(TEXTS[lang]["sponsor_title"], reply_markup=kb, parse_mode="HTML")

@router.message(F.text.in_({"🤝 Спонсоры", "🤝 Демеушілер"}))
@router.callback_query(F.data == "menu_sponsors")
async def sponsors_handler(event: Message | CallbackQuery):
    lang = await get_user_language(event.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👦 Братья / Бауырлар", callback_data="list_brothers_0")],
        [InlineKeyboardButton(text="👧 Сестры / Әпкелер", callback_data="list_sisters_0")]
    ])
    if isinstance(event, Message):
        await event.answer(TEXTS[lang]["sponsors_title"], reply_markup=kb)
    else:
        await event.message.edit_text(TEXTS[lang]["sponsors_title"], reply_markup=kb)
        await event.answer()

@router.message(F.text.in_({"📅 Расписание", "📅 Кесте"}))
async def schedule_menu(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    await message.answer(TEXTS[lang]["schedule_title"], reply_markup=get_schedule_kb(), parse_mode="HTML")

@router.callback_query(F.data.startswith("s_"))
async def schedule_callback(callback: CallbackQuery):
    data = callback.data
    lang = await get_user_language(callback.from_user.id)
    
    if data == "s_back":
        await callback.message.edit_text(TEXTS[lang]["schedule_title"], reply_markup=get_schedule_kb(), parse_mode="HTML")
        await callback.answer()
        return

    text = SCHEDULE_DATA.get(data, "") + TEXTS[lang]["help_line"]
    kb_buttons = [[]]
    if data in SCHEDULE_URLS:
        kb_buttons.append([InlineKeyboardButton(text="📍 Открыть в 2GIS", url=SCHEDULE_URLS[data])])
    if data == "s_other":
        kb_buttons = [
            [InlineKeyboardButton(text="📍 Новые Очки (2GIS)", url="https://2gis.kz/almaty/geo/9430047374988153/76.950690,43.262199")],
            [InlineKeyboardButton(text="📍 Турксиб (2GIS)", url="https://2gis.kz/almaty/geo/9430047374991567/76.955136,43.330053")],
            [InlineKeyboardButton(text="📍 Талхиз (2GIS)", url="https://2gis.kz/almaty/geo/70000001045475756/77.234246,43.317702")]
        ]
    kb_buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="s_back")])
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons), parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()

@router.message(F.text.in_({"❓ Помощь", "❓ Көмек"}))
async def help_menu(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="👤 Позвать служащего / Қызметкерді шақыру", callback_data="call_servant")]])
    await message.answer(TEXTS[lang]["help_title"], reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    lang = await get_user_language(callback.from_user.id)
    try: await callback.message.delete()
    except: pass
    await callback.message.answer("🏠 <b>Главное меню / Басты мәзір</b>", reply_markup=get_menu_kb(lang), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "call_servant")
async def call_servant(callback: CallbackQuery):
    user = callback.from_user
    lang = await get_user_language(user.id)
    user_link = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"
    username = f" (@{user.username})" if user.username else ""
    
    alert_text = TEXTS[lang]["servant_alert"].format(user_link=user_link, username=username, user=user)
    for sid in SERVANT_CHAT_IDS:
        try: await callback.bot.send_message(chat_id=sid, text=alert_text, parse_mode="HTML")
        except Exception as e: logging.error(f"Ошибка отправки служащему {sid}: {e}")

    await callback.message.answer(TEXTS[lang]["servant_success"])
    await callback.answer()

@router.message(StateFilter(None), F.text)
async def ai_handler(message: types.Message, state: FSMContext):
    all_btns = TEXTS["ru"]["btns"] + TEXTS["kk"]["btns"] + ["Главное меню", "Басты мәзір"]
    if message.text in all_btns: return

    lang = await get_user_language(message.from_user.id)
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    ai_response = await ask_ai_for_beginner(message.from_user.id, message.text)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="👤 Позвать служащего / Қызметкерді шақыру", callback_data="call_servant")]])
    await message.answer(ai_response, parse_mode="Markdown", reply_markup=kb)