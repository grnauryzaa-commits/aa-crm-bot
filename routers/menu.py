from datetime import datetime
import logging
import psycopg2
import asyncio

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from config import DATABASE_URL
from database import get_user_language, set_user_language
from ai_helper import ask_ai_for_beginner

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

def clean_reflection_text(raw_text: str) -> str:
    """Очистка текста размышлений от мусора и ссылок сайта"""
    if not raw_text:
        return ""
    
    lines = raw_text.splitlines()
    cleaned_lines = []
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        if "www.Mos-Nach.ru" in line_str or "http://" in line_str or "https://" in line_str:
            continue
        if "Поделиться:" in line_str or line_str in ["Twitter", "Facebook", "Vkontakte", "WhatsApp", "Telegram", "EMail"]:
            continue
        if "Анонимные Алкоголики." in line_str:
            continue
        cleaned_lines.append(line_str)
        
    return "\n".join(cleaned_lines)

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
        def fetch_reflection():
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("SELECT title, text FROM reflections_archive WHERE day = %s AND month = %s", (today.day, today.month))
            row = cur.fetchone()
            cur.close()
            conn.close()
            return row

        row = await asyncio.to_thread(fetch_reflection)

        if row:
            title, raw_text = row[0], row[1]
            cleaned_text = clean_reflection_text(raw_text)

            header = "📖 <b>Ежедневное размышление</b>" if lang == 'ru' else "📖 <b>Күнделікті ой-толғау</b>"
            text = f"{header}\n\n"
            if title:
                text += f"<b>{title}</b>\n\n"
            text += f"{cleaned_text}"

            await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(lang))
        else:
            msg = "На сегодня размышления не найдены в базе." if lang == 'ru' else "Бүгінге ой-толғаулар табылмады."
            await message.answer(msg, reply_markup=get_main_menu_keyboard(lang))
            
    except Exception as e:
        logging.error(f"Ошибка получения размышлений: {e}")
        msg = "Произошла ошибка при получении размышлений." if lang == 'ru' else "Ой-толғауларды алу кезінде қате орын алды."
        await message.answer(msg, reply_markup=get_main_menu_keyboard(lang))

# ЗАГЛУШКИ/ХЕНДЛЕРЫ ДЛЯ ОСТАЛЬНЫХ КНОПОК, ЧТОБЫ ОНИ НЕ ВИСЕЛИ
@router.message(F.text.in_({"🙏 11 Шаг", "🙏 11 Қадам"}))
async def btn_step11_handler(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    msg = "Раздел 11 Шага в разработке или подключается." if lang == 'ru' else "11 Қадам бөлімі әзірленуде."
    await message.answer(msg, reply_markup=get_main_menu_keyboard(lang))

@router.message(F.text.in_({"➕ Стать спонсором", "➕ Демеуші болу"}))
async def btn_sponsor_handler(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    msg = "Раздел спонсорства." if lang == 'ru' else "Демеушілік бөлімі."
    await message.answer(msg, reply_markup=get_main_menu_keyboard(lang))

@router.message(F.text.in_({"🤝 Спонсоры", "🤝 Демеушілер"}))
async def btn_sponsors_handler(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    msg = "Список спонсоров." if lang == 'ru' else "Демеушілер тізімі."
    await message.answer(msg, reply_markup=get_main_menu_keyboard(lang))

@router.message(F.text.in_({"📅 Расписание", "📅 Кесте"}))
async def btn_schedule_handler(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    msg = "Расписание групп." if lang == 'ru' else "Топтар кестесі."
    await message.answer(msg, reply_markup=get_main_menu_keyboard(lang))

@router.message(F.text.in_({"❓ Помощь", "❓ Көмек"}))
async def btn_help_handler(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    msg = "Помощь по использованию бота." if lang == 'ru' else "Боты қолдану бойынша көмек."
    await message.answer(msg, reply_markup=get_main_menu_keyboard(lang))

@router.message(StateFilter(None), F.text)
async def handle_beginner_questions(message: types.Message, state: FSMContext):
    if message.chat.type != "private":
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    ai_response = await ask_ai_for_beginner(message.from_user.id, message.text)
    
    servant_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Позвать живого служащего / Қызметкерді шақыру", callback_data="call_servant")]
        ]
    )
    await message.answer(ai_response, parse_mode="Markdown", reply_markup=servant_keyboard)