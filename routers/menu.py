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
from database import get_user_language, set_user_language, get_main_menu_keyboard

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

@router.message(F.text.in_({"➕ Стать спонсором", "➕ Демеуші болу"}))
async def become_sponsors_menu_direct(message: Message, state: FSMContext):
    await state.clear()
    lang = await get_user_language(message.from_user.id)
    
    titles = {
        "ru": "➕ <b>Стать спонсором в АА</b>\n\nСпонсор — это человек, который прошел Шаги и готов делиться опытом с другими.",
        "kk": "➕ <b>АА-да демеуші болу</b>\n\nДемеуші — Қадамдардан өткен және басқалармен тәжірибе бөлісуге дайын адам."
    }
    btn_fills = {
        "ru": "📝 Заполнить анкету спонсора",
        "kk": "📝 Демеуші сауалнамасын толтыру"
    }
    btn_backs = {
        "ru": "🔙 Назад в меню",
        "kk": "🔙 Мәзірге оралу"
    }
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=btn_fills[lang], callback_data="start_sponsor_registration")],
            [InlineKeyboardButton(text=btn_backs[lang], callback_data="back_to_menu")]
        ]
    )
    await message.answer(titles[lang], reply_markup=keyboard, parse_mode="HTML")

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
    # Заглушка или вызов шага 11 под язык
    await message.answer("11 Шаг", reply_markup=get_main_menu_keyboard(lang))

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

@router.message(F.text.in_({"📅 Расписание", "🗓 Расписание", "🗓 Кесте", "📅 Кесте"}))
async def show_schedule_menu(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Онлайн группы", callback_data="s_online")],
        [InlineKeyboardButton(text="📍 Алматы: Жубанова 3а", callback_data="s_zhub")],
        [InlineKeyboardButton(text="📍 Алматы: Зенкова 24", callback_data="s_zenk")],
        [InlineKeyboardButton(text="📍 Алматы: Тимирязева 42", callback_data="s_tim")],
        [InlineKeyboardButton(text="📍 Каскелен: Нур-Жанат", callback_data="s_kaskelen")],
        [InlineKeyboardButton(text="📍 Другие локации", callback_data="s_other")]
    ])
    await message.answer("📅 <b>Расписание собраний АА</b>\nВыберите локацию:", reply_markup=kb, parse_mode="HTML")

@router.message(F.text.in_({"? Помощь", "❓ Помощь", "❓ Көмек", "? Көмек"}))
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
            await callback.bot.send_message(chat_id=servant_id, text=alert_text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление служащему: {e}")

    await callback.message.answer(t["servant_success"])
    await callback.answer()

@router.message(StateFilter(None), F.text)
async def handle_beginner_questions(message: types.Message, state: FSMContext):
    menu_buttons = [
        "📖 Ежедневные размышления", "🙏 11 Шаг", 
        "➕ Стать спонсором", "🤝 Спонсоры", 
        "📅 Расписание", "🗓 Расписание", "❓ Помощь", "? Помощь", "🏠 Главное меню", "Главное меню",
        "📖 Күнделікті ой-толғаулар", "🙏 11 Қадам", 
        "➕ Демеуші болу", "🤝 Демеушілер", 
        "📅 Кесте", "🗓 Кесте", "❓ Көмек", "? Көмек", "🏠 Басты мәзір", "Басты мәзір",
        "🌐 Язык: Русский", "🌐 Тіл: Қазақша"
    ]
    if message.text in menu_buttons:
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    ai_response = await ask_ai_for_beginner(message.from_user.id, message.text)
    
    lang = await get_user_language(message.from_user.id)
    help_text_btn = "👤 Позвать живого служащего" if lang == 'ru' else "👤 Тірі қызметкерді шақыру"
    
    servant_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=help_text_btn, callback_data="call_servant")]
        ]
    )
    await message.answer(ai_response, parse_mode="Markdown", reply_markup=servant_keyboard)