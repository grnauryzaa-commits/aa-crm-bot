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
        "start_greeting": (
            "Приветствую! Добро пожаловать в бот сообщества Анонимных Алкоголиков.\n\n"
            "🤖 Вы можете задать мне любой вопрос о программе АА своими словами, и я постараюсь помочь.\n\n"
            "👇 <b>Главное меню всегда находится внизу экрана.</b> Нажимайте на нужные кнопки:"
        ),
        "menu": "🏠 <b>Главное меню</b>\n\nВыберите нужный раздел внизу 👇",
        "choose_lang": "🌐 Выберите язык интерфейса и общения с ботом:",
        "lang_changed": "✅ Язык успешно изменен на русский!",
        "btn_reflection": "📖 Ежедневные размышления",
        "btn_step11": "🙏 11 Шаг",
        "btn_sponsor": "➕ Стать спонсором",
        "btn_sponsors": "🤝 Спонсоры",
        "btn_schedule": "📅 Расписание",
        "btn_help": "❓ Помощь",
        "btn_lang": "🌐 Язык: Русский",
        "sponsors_title": "👥 Выберите список:",
        "sponsor_brothers": "👦 Братья",
        "sponsor_sisters": "👧 Сестры",
        "help_title": "❓ <b>Помощь и поддержка</b>\n\nЕсли вам тяжело или у вас срочный вопрос — вы можете задать его мне в чате или позвать дежурного служащего.",
        "help_btn": "👤 Позвать живого служащего",
        "servant_alert": "🚨 <b>Новый запрос о помощи!</b>\n\nПользователь: {user_link}{username_text}\nID: <code>{user_id}</code>\nНажал кнопку «Позвать живого служащего».",
        "servant_success": "🙏 Ваша заявка принята. Дежурный служащий сообщества уведомлен и свяжется с вами в ближайшее время.",
        "step11_title": "🙏 <b>11 Шаг программы АА</b>\n\nВыберите нужную практику:",
        "step11_morning": "🌅 Утренняя молитва",
        "step11_evening": "🌙 Вечерняя молитва"
    },
    "kk": {
        "start_greeting": (
            "Қош келдіңіз! Анонимді Алкоголиктер қауымдастығының ботына қош келдіңіз.\n\n"
            "🤖 Сіз маған АА бағдарламасы туралы кез келген сұрақты өз сөзіңізбен қоя аласыз, мен көмектесуге тырысамын.\n\n"
            "👇 <b>Басты мәзір әрқашан экранның төменгі бөлігінде орналасқан.</b> Қажетті түймелерді басыңыз:"
        ),
        "menu": "🏠 <b>Басты мәзір</b>\n\nТөменден қажетті бөлімді таңдаңыз 👇",
        "choose_lang": "🌐 Тілді таңдаңыз / Выберите язык:",
        "lang_changed": "✅ Тіл қазақ тіліне өзгертілді!",
        "btn_reflection": "📖 Күнделікті ой-толғаулар",
        "btn_step11": "🙏 11 Қадам",
        "btn_sponsor": "➕ Демеуші болу",
        "btn_sponsors": "🤝 Демеушілер",
        "btn_schedule": "📅 Кесте",
        "btn_help": "❓ Көмек",
        "btn_lang": "🌐 Тіл: Қазақша",
        "sponsors_title": "👥 Тізімді таңдаңыз:",
        "sponsor_brothers": "👦 Бауырлар",
        "sponsor_sisters": "👧 Әпкелер",
        "help_title": "❓ <b>Көмек және қолдау</b>\n\nЕгер сізге қиын болса немесе шұғыл сұрағыңыз болса — оны маған чатта қоюға немесе кезекші қызметкерді шақыруға болады.",
        "help_btn": "👤 Тірі қызметкерді шақыру",
        "servant_alert": "🚨 <b>Жаңа көмек сұрау!</b>\n\nПайдаланушы: {user_link}{username_text}\nID: <code>{user_id}</code>\n«Тірі қызметкерді шақыру» түймесін басты.",
        "servant_success": "🙏 Өтінішіңіз қабылданды. Қауымдастықтың кезекші қызметкері хабардар етілді және жақын арада сізбен байланысады.",
        "step11_title": "🙏 <b>АА бағдарламасының 11-ші қадамы</b>\n\nҚажетті тәжірибені таңдаңыз:",
        "step11_morning": "🌅 Таңғы дұға",
        "step11_evening": "🌙 Кешкі дұға"
    }
}

def get_main_menu_keyboard(lang='ru'):
    t = TEXTS[lang]
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=t["btn_reflection"])],
            [types.KeyboardButton(text=t["btn_step11"]), types.KeyboardButton(text=t["btn_sponsor"])],
            [types.KeyboardButton(text=t["btn_sponsors"]), types.KeyboardButton(text=t["btn_schedule"])],
            [types.KeyboardButton(text=t["btn_help"]), types.KeyboardButton(text=t["btn_lang"])]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел / Бөлімді таңдаңыз 👇"
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
    filtered = [line for line in lines if not any(f in line.casefold() for f in [x.casefold() for x in forbidden])]
    
    if len(filtered) > 0 and f"{today.day}" in filtered[0] and len(filtered[0]) < 25:
        filtered.pop(0)
    if len(filtered) > 0 and f"{today.day}" in filtered[0] and len(filtered[0]) < 25:
        filtered.pop(0)
    
    body = "\n\n".join(filtered)
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", 
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    escaped_body = html.escape(body)
    return f"📖 <b>Ежедневные размышления АА</b>\n\n📋 <b>{today.day} {months[today.month - 1]}</b>\n\n{escaped_body}"

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    lang = await get_user_language(message.from_user.id)
    await message.answer(TEXTS[lang]["start_greeting"], reply_markup=get_main_menu_keyboard(lang), parse_mode="HTML")

@router.message(F.text.in_({"🏠 Главное меню", "Главное меню", "🏠 Басты мәзір", "Басты мәзір"}))
async def cmd_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    lang = await get_user_language(message.from_user.id)
    await message.answer(TEXTS[lang]["menu"], reply_markup=get_main_menu_keyboard(lang), parse_mode="HTML")

@router.message(F.text.in_({"🌐 Язык: Русский", "🌐 Тіл: Қазақша"}))
async def language_menu_handler(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru")],
        [InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="set_lang_kk")]
    ])
    await message.answer(TEXTS[lang]["choose_lang"], reply_markup=keyboard)

@router.callback_query(F.data.startswith("set_lang_"))
async def set_language_callback(callback: types.CallbackQuery):
    lang = callback.data.split("_")[2]
    await set_user_language(callback.from_user.id, lang)
    t = TEXTS[lang]
    await callback.message.answer(t["lang_changed"], reply_markup=get_main_menu_keyboard(lang))
    await callback.answer()

@router.message(F.text.in_({"📖 Ежедневные размышления", "📖 Күнделікті ой-толғаулар"}))
async def show_daily_reflection(message: types.Message):
    today = datetime.now()
    lang = await get_user_language(message.from_user.id)
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT text FROM reflections_archive WHERE day = %s AND month = %s", (today.day, today.month))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            text = format_reflection_text(row[0], today)
            await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(lang))
        else:
            msg = "На сегодня размышления не найдены в базе." if lang == 'ru' else "Бүгінге ой-толғаулар табылмады."
            await message.answer(msg, reply_markup=get_main_menu_keyboard(lang))
    except Exception as e:
        logging.error(f"Ошибка получения размышлений: {e}")
        msg = "Произошла ошибка при получении размышлений." if lang == 'ru' else "Ой-толғауларды алу кезінде қате орын алды."
        await message.answer(msg, reply_markup=get_main_menu_keyboard(lang))

@router.message(F.text.in_({"🙏 11 Шаг", "🙏 11 Қадам"}))
async def step_eleven_menu(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    t = TEXTS[lang]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t["step11_morning"], callback_data="get_morning_prayer")],
            [InlineKeyboardButton(text=t["step11_evening"], callback_data="get_evening_prayer")]
        ]
    )
    await message.answer(t["step11_title"], reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data == "get_morning_prayer")
async def send_morning_callback(callback: types.CallbackQuery):
    await callback.message.answer(MORNING_PRAYER_TEXT, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "get_evening_prayer")
async def send_evening_callback(callback: types.CallbackQuery):
    await callback.message.answer(EVENING_PRAYER_TEXT, parse_mode="HTML")
    await callback.answer()

@router.message(F.text.in_({"🤝 Спонсоры", "🤝 Демеушілер"}))
@router.callback_query(F.data == "menu_sponsors")
async def sponsors_menu_handler(event: Message | CallbackQuery):
    lang = await get_user_language(event.from_user.id)
    t = TEXTS[lang]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["sponsor_brothers"], callback_data="list_brothers_0")],
        [InlineKeyboardButton(text=t["sponsor_sisters"], callback_data="list_sisters_0")]
    ])
    if isinstance(event, Message):
        await event.answer(t["sponsors_title"], reply_markup=keyboard)
    else:
        await event.message.edit_text(t["sponsors_title"], reply_markup=keyboard)
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

@router.message(F.text.in_({"📅 Расписание", "📅 Кесте"}))
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

@router.message(F.text.in_({"❓ Помощь", "❓ Көмек"}))
async def help_section_handler(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    t = TEXTS[lang]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t["help_btn"], callback_data="call_servant")]
        ]
    )
    await message.answer(t["help_title"], reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(callback: types.CallbackQuery):
    lang = await get_user_language(callback.from_user.id)
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(
        TEXTS[lang]["menu"],
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer("Возврат в меню")

@router.callback_query(F.data == "call_servant")
async def call_servant_callback(callback: types.CallbackQuery):
    user = callback.from_user
    lang = await get_user_language(user.id)
    t = TEXTS[lang]
    user_link = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"
    username_text = f" (@{user.username})" if user.username else ""
    
    alert_text = t["servant_alert"].format(
        user_link=user_link, 
        username_text=username_text, 
        user_id=user.id
    )

    for servant_id in SERVANT_CHAT_IDS:
        try:
            await callback.bot.send_message(
                chat_id=servant_id,
                text=alert_text,
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление служащему: {e}")

    await callback.message.answer(t["servant_success"])
    await callback.answer()

@router.message(StateFilter(None), F.text)
async def handle_beginner_questions(message: types.Message, state: FSMContext):
    menu_buttons = [
        "📖 Ежедневные размышления", "🙏 11 Шаг", 
        "➕ Стать спонсором", "🤝 Спонсоры", 
        "📅 Расписание", "❓ Помощь", "🏠 Главное меню", "Главное меню",
        "📖 Күнделікті ой-толғаулар", "🙏 11 Қадам", 
        "➕ Демеуші болу", "🤝 Демеушілер", 
        "📅 Кесте", "❓ Көмек", "🏠 Басты мәзір", "Басты мәзір",
        "🌐 Язык: Русский", "🌐 Тіл: Қазақша"
    ]
    if message.text in menu_buttons or "Демеуші болу" in message.text or "Стать спонсором" in message.text:
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    ai_response = await ask_ai_for_beginner(message.from_user.id, message.text)
    
    servant_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Позвать живого служащего", callback_data="call_servant")]
        ]
    )
    await message.answer(ai_response, parse_mode="Markdown", reply_markup=servant_keyboard)