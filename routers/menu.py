import html
import logging
from datetime import datetime
import psycopg2
from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import DATABASE_URL, SERVANT_CHAT_IDS
from database import get_user_language, set_user_language
from routers.reflections import EVENING_PRAYER_TEXT, MORNING_PRAYER_TEXT
from routers.ai_helper import ask_ai_for_beginner

router = Router()

T = {
    "ru": {
        "start": "Приветствую! Добро пожаловать в бот АА.\n\n🤖 Задайте любой вопрос о программе, и я помогу.\n\n👇 Главное меню внизу:",
        "menu": "🏠 <b>Главное меню</b>",
        "lang_ch": "✅ Язык изменен на русский!",
        "help_t": "❓ <b>Помощь</b>\n\nЕсли тяжело — задайте вопрос или позовите дежурного.",
        "help_b": "👤 Позвать живого служащего",
        "s_succ": "🙏 Заявка принята. Дежурный свяжется с вами.",
        "s_alert": "🚨 <b>Запрос помощи!</b>\nПользователь: {user_link}\nID: <code>{user_id}</code>",
        "btns": [
            "📖 Ежедневные размышления",
            "🙏 11 Шаг",
            "➕ Стать спонсором",
            "🤝 Спонсоры",
            "📅 Расписание",
            "❓ Помощь",
            "🏠 Главное меню",
            "Главное меню",
        ],
    },
    "kk": {
        "start": "Қош келдіңіз! АА ботына қош келдіңіз.\n\n🤖 Сұрағыңызды қойыңыз, көмектесемін.\n\n👇 Басты мәзір төменде:",
        "menu": "🏠 <b>Басты мәзір</b>",
        "lang_ch": "✅ Тіл қазақ тіліне өзгертілді!",
        "help_t": "❓ <b>Көмек</b>\n\nСұрақ қойыңыз немесе кезекшіні шақырыңыз.",
        "help_b": "👤 Тірі қызметкерді шақыру",
        "s_succ": "🙏 Өтініш қабылданды. Кезекші байланысады.",
        "s_alert": "🚨 <b>Көмек сұрау!</b>\nПайдаланушы: {user_link}\nID: <code>{user_id}</code>",
        "btns": [
            "📖 Күнделікті ой-толғаулар",
            "🙏 11 Қадам",
            "➕ Демеуші болу",
            "🤝 Демеушілер",
            "📅 Кесте",
            "❓ Көмек",
            "🏠 Басты мәзір",
            "Басты мәзір",
        ],
    },
}

# Обратная совместимость для других файлов, которые ищут эту функцию
def get_main_menu_keyboard(lang="ru"):
    b = T[lang]["btns"]
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=b[0])],
            [types.KeyboardButton(text=b[1]), types.KeyboardButton(text=b[2])],
            [types.KeyboardButton(text=b[3]), types.KeyboardButton(text=b[4])],
            [
                types.KeyboardButton(text=b[5]),
                types.KeyboardButton(text="🌐 Язык: Русский" if lang == "ru" else "🌐 Тіл: Қазақша"),
            ],
        ],
        resize_keyboard=True,
    )

get_kb = get_main_menu_keyboard


@router.message(Command("start"))
@router.message(F.text.in_({"🏠 Главное меню", "Главное меню", "🏠 Басты мәзір", "Басты мәзір"}))
async def cmd_start_menu(message: types.Message, state: FSMContext):
    await state.clear()
    lang = await get_user_language(message.from_user.id)
    text = T[lang]["start"] if message.text == "/start" else T[lang]["menu"]
    await message.answer(text, reply_markup=get_kb(lang), parse_mode="HTML")


@router.message(F.text.startswith("🌐"))
async def lang_menu(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang_kk")],
        ]
    )
    await message.answer("🌐 Выберите язык / Тілді таңдаңыз:", reply_markup=kb)


@router.callback_query(F.data.startswith("lang_"))
async def set_lang(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    await set_user_language(callback.from_user.id, lang)
    await callback.message.answer(T[lang]["lang_ch"], reply_markup=get_kb(lang))
    await callback.answer()


@router.message(F.text.in_({"📖 Ежедневные размышления", "📖 Күнделікті ой-толғаулар"}))
async def daily_ref(message: types.Message):
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
            body = html.escape("\n\n".join([l.strip() for l in row[0].split("\n") if l.strip()][:15]))
            await message.answer(f"📖 <b>Размышления</b>\n\n{body}", reply_markup=get_kb(lang), parse_mode="HTML")
        else:
            await message.answer("Не найдено", reply_markup=get_kb(lang))
    except Exception as e:
        logging.error(e)
        await message.answer("Ошибка БД", reply_markup=get_kb(lang))


@router.message(F.text.in_({"🙏 11 Шаг", "🙏 11 Қадам"}))
async def step11(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌅 Утренняя молитва", callback_data="pr_morn")],
            [InlineKeyboardButton(text="🌙 Вечерняя молитва", callback_data="pr_even")],
        ]
    )
    await message.answer("🙏 11 Шаг программы:", reply_markup=kb)


@router.callback_query(F.data.in_({"pr_morn", "pr_even"}))
async def send_prayer(callback: CallbackQuery):
    text = MORNING_PRAYER_TEXT if callback.data == "pr_morn" else EVENING_PRAYER_TEXT
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.message(F.text.in_({"➕ Стать спонсором", "➕ Демеуші болу"}))
async def sponsor_menu(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Заполнить анкету", callback_data="start_sponsor_registration")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")],
        ]
    )
    await message.answer("➕ <b>Стать спонсором в АА</b>", reply_markup=kb, parse_mode="HTML")


@router.message(F.text.in_({"🤝 Спонсоры", "🤝 Демеушілер"}))
@router.callback_query(F.data == "menu_sponsors")
async def sponsors_list(event: Message | CallbackQuery):
    lang = await get_user_language(event.from_user.id)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👦 Братья", callback_data="list_brothers_0")],
            [InlineKeyboardButton(text="👧 Сестры", callback_data="list_sisters_0")],
        ]
    )
    if isinstance(event, Message):
        await event.answer("👥 Выберите список:", reply_markup=kb)
    else:
        await event.message.edit_text("👥 Выберите список:", reply_markup=kb)
        await event.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_menu(callback: CallbackQuery):
    lang = await get_user_language(callback.from_user.id)
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(T[lang]["menu"], reply_markup=get_kb(lang), parse_mode="HTML")
    await callback.answer()


def get_sch_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Онлайн группы", callback_data="s_online")],
            [InlineKeyboardButton(text="📍 Жубанова 3а", callback_data="s_zhub")],
            [InlineKeyboardButton(text="📍 Зенкова 24", callback_data="s_zenk")],
            [InlineKeyboardButton(text="📍 Тимирязева 42", callback_data="s_tim")],
            [InlineKeyboardButton(text="📍 Каскелен", callback_data="s_kaskelen")],
            [InlineKeyboardButton(text="📍 Другие локации", callback_data="s_other")],
        ]
    )


@router.message(F.text.in_({"📅 Расписание", "📅 Кесте"}))
async def schedule_menu(message: types.Message):
    await message.answer("📅 <b>Расписание собраний АА</b>\nВыберите локацию:", reply_markup=get_sch_kb(), parse_mode="HTML")


@router.callback_query(F.data.startswith("s_"))
async def schedule_cb(callback: CallbackQuery):
    data = callback.data
    kb_back = [[InlineKeyboardButton(text="⬅️ Назад", callback_data="s_back")]]
    help_t = "\n\n📞 Горячая линия: +7 708 317 17 69"

    if data == "s_back":
        return await callback.message.edit_text("📅 <b>Расписание собраний АА</b>\nВыберите локацию:", reply_markup=get_sch_kb(), parse_mode="HTML")

    texts = {
        "s_online": "🌐 <b>ОНЛАЙН Зона</b>\n• Пробуждение: Вт, Чт, Сб 21:00\n• Бірлік (каз): Чт 21:00" + help_t,
        "s_zhub": "🏢 <b>Жубанова 3а</b>\n• Виктория: Вт, Чт 19:30, Сб 19:00\n• Шапагат: Пн, Ср 19:00" + help_t,
        "s_zenk": "🏢 <b>Зенкова 24</b>\n• 8 марта: Ежедневно 19:00" + help_t,
        "s_tim": "🏢 <b>Тимирязева 42</b>\n• Наурыз: Вт, Чт, Пт, Сб 19:00" + help_t,
        "s_kaskelen": "🏢 <b>Каскелен (ТД Нур-Жанат)</b>\n• Туран: Пн, Ср, Сб 17:00" + help_t,
        "s_other": "📍 <b>Другие локации</b>\n• Аксай, Новые Очки, Боралдай, Талгар" + help_t,
    }
    await callback.message.edit_text(texts.get(data, "Информация"), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_back), parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()


@router.message(F.text.in_({"❓ Помощь", "❓ Көмек"}))
async def help_handler(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=T[lang]["help_b"], callback_data="call_servant")]])
    await message.answer(T[lang]["help_t"], reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "call_servant")
async def call_servant(callback: CallbackQuery):
    user = callback.from_user
    lang = await get_user_language(user.id)
    user_link = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"
    alert = T[lang]["s_alert"].format(user_link=user_link, user_id=user.id)

    for sid in SERVANT_CHAT_IDS:
        try:
            await callback.bot.send_message(chat_id=sid, text=alert, parse_mode="HTML")
        except Exception:
            pass

    await callback.message.answer(T[lang]["s_succ"])
    await callback.answer()


@router.message(StateFilter(None), F.text)
async def ai_handler(message: types.Message, state: FSMContext):
    lang = await get_user_language(message.from_user.id)
    if message.text in T[lang]["btns"] or message.text.startswith("🌐"):
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    ai_response = await ask_ai_for_beginner(message.from_user.id, message.text)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=T[lang]["help_b"], callback_data="call_servant")]])
    await message.answer(ai_response, parse_mode="Markdown", reply_markup=kb)