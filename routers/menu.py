from datetime import datetime
import html
import logging
from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from config import DATABASE_URL, SERVANT_CHAT_IDS
from database import get_user_language, set_user_language
from routers.reflections import (
    EVENING_PRAYER_TEXT_KK,
    EVENING_PRAYER_TEXT_RU,
    MORNING_PRAYER_TEXT_KK,
    MORNING_PRAYER_TEXT_RU,
    format_reflection_text,
)
import psycopg2

from .ai_helper import ask_ai_for_beginner

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
        "btn_literature": "📖 Литература АА",
        "sponsors_title": "👥 Выберите список:",
        "sponsor_brothers": "👦 Братья",
        "sponsor_sisters": "👧 Сестры",
        "help_title": (
            "❓ <b>Помощь и поддержка</b>\n\nЕсли вам тяжело или у вас срочный"
            " вопрос — вы можете задать его мне в чате или позвать дежурного"
            " служащего."
        ),
        "help_btn": "👤 Позвать живого служащего",
        "servant_alert": (
            "🚨 <b>Новый запрос о помощи!</b>\n\nПользователь:"
            " {user_link}{username_text}\nID: <code>{user_id}</code>\nНажал"
            " кнопку «Позвать живого служащего»."
        ),
        "servant_success": (
            "🙏 Ваша заявка принята. Дежурный служащий сообщества уведомлен и"
            " свяжется с вами в ближайшее время."
        ),
        "step11_title": "🙏 <b>11 Шаг программы АА</b>\n\nВыберите нужную практику:",
        "step11_morning": "🌅 Утренняя молитва",
        "step11_evening": "🌙 Вечерняя молитва",
    },
    "kk": {
        "start_greeting": (
            "Қош келдіңіз! Анонимді Алкоголиктер қауымдастығының ботына қош"
            " келдіңіз.\n\n🤖 Сіз маған АА бағдарламасы туралы кез келген"
            " сұрақты өз сөзіңізбен қоя аласыз, мен көмектесуге тырысамын.\n\n👇"
            " <b>Басты мәзір әрқашан экранның төменгі бөлігінде орналасқан.</b>"
            " Қажетті түймелерді басыңыз:"
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
        "btn_literature": "📖 АА Әдебиеті",
        "sponsors_title": "👥 Тізімді таңдаңыз:",
        "sponsor_brothers": "👦 Бауырлар",
        "sponsor_sisters": "👧 Әпкелер",
        "help_title": (
            "❓ <b>Көмек және қолдау</b>\n\nЕгер сізге қиын болса немесе шұғыл"
            " сұрағыңыз болса — оны маған чатта қоюға немесе кезекші қызметкерді"
            " шақыруға болады."
        ),
        "help_btn": "👤 Тірі қызметкерді шақыру",
        "servant_alert": (
            "🚨 <b>Жаңа көмек сұрау!</b>\n\nПайдаланушы:"
            " {user_link}{username_text}\nID: <code>{user_id}</code>\n«Тірі"
            " қызметкерді шақыру» түймесін басты."
        ),
        "servant_success": (
            "🙏 Өтінішіңіз қабылданды. Қауымдастықтың кезекші қызметкері"
            " хабардар етілді және жақын арада сізбен байланысады."
        ),
        "step11_title": (
            "🙏 <b>АА бағдарламасының 11-ші қадамы</b>\n\nҚажетті тәжірибені"
            " таңдаңыз:"
        ),
        "step11_morning": "🌅 Таңғы дұға",
        "step11_evening": "🌙 Кешкі дұға",
    },
}


def get_main_menu_keyboard(lang="ru"):
    t = TEXTS[lang]
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=t["btn_reflection"])],
            [
                types.KeyboardButton(text=t["btn_step11"]),
                types.KeyboardButton(text=t["btn_sponsor"]),
            ],
            [
                types.KeyboardButton(text=t["btn_sponsors"]),
                types.KeyboardButton(text=t["btn_schedule"]),
            ],
            [
                types.KeyboardButton(text=t["btn_help"]),
                types.KeyboardButton(text=t["btn_lang"]),
            ],
            [types.KeyboardButton(text=t["btn_literature"])],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел / Бөлімді таңдаңыз 👇",
    )


@router.message(F.chat.type == "private", Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    lang = await get_user_language(message.from_user.id)
    if not lang:
        lang = "ru"
    await message.answer(
        TEXTS[lang]["start_greeting"],
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="HTML",
    )


@router.message(
    F.chat.type == "private",
    F.text.in_(
        {"🏠 Главное меню", "Главное меню", "🏠 Басты мәзір", "Басты мәзір"}
    ),
)
async def cmd_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    lang = await get_user_language(message.from_user.id)
    if not lang:
        lang = "ru"
    await message.answer(
        TEXTS[lang]["menu"],
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="HTML",
    )


@router.message(
    F.chat.type == "private",
    F.text.in_({"🌐 Язык: Русский", "🌐 Тіл: Қазақша"}),
)
async def language_menu_handler(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    if not lang:
        lang = "ru"
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🇷🇺 Русский", callback_data="set_lang_ru"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="🇰🇿 Қазақша", callback_data="set_lang_kk"
                )
            ],
        ]
    )
    await message.answer(TEXTS[lang]["choose_lang"], reply_markup=keyboard)


@router.callback_query(F.data.startswith("set_lang_"))
async def set_language_callback(callback: types.CallbackQuery):
    if callback.message.chat.type != "private":
        await callback.answer()
        return
    lang = callback.data.split("_")[2]
    await set_user_language(callback.from_user.id, lang)
    t = TEXTS[lang]
    await callback.message.answer(
        t["lang_changed"], reply_markup=get_main_menu_keyboard(lang)
    )
    await callback.answer()


@router.message(
    F.chat.type == "private",
    (
        F.text.in_({"➕ Стать спонсором", "➕ Демеуші болу"})
        | F.text.contains("Демеуші болу")
        | F.text.contains("Стать спонсором")
    ),
)
async def become_sponsors_menu_direct(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id

    lang = await get_user_language(user_id)
    if not lang:
        lang = "ru"

    titles = {
        "ru": (
            "➕ <b>Стать спонсором в АА</b>\n\nСпонсор — это человек, который"
            " прошел Шаги и готов делиться опытом с другими."
        ),
        "kk": (
            "➕ <b>АА-да демеуші болу</b>\n\nДемеуші — Қадамдардан өткен және"
            " басқалармен тәжірибе бөлісуге дайын адам."
        ),
    }
    btn_fills = {
        "ru": "📝 Заполнить анкету спонсора",
        "kk": "📝 Демеуші сауалнамасын толтыру",
    }
    btn_backs = {"ru": "🔙 Назад в меню", "kk": "🔙 Мәзірге оралу"}

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=btn_fills[lang],
                    callback_data=f"start_sponsor_registration_{lang}",
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=btn_backs[lang], callback_data=f"back_to_menu_{lang}"
                )
            ],
        ]
    )
    await message.answer(titles[lang], reply_markup=keyboard, parse_mode="HTML")
    

@router.message(
    F.chat.type == "private",
    F.text.in_({"📖 Ежедневные размышления", "📖 Күнделікті ой-толғаулар"}),
)
async def show_daily_reflection(message: types.Message):
    today = datetime.now()
    lang = await get_user_language(message.from_user.id)
    if not lang:
        lang = "ru"

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        if lang == "kk":
            months_map_kk = {
                1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
                5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
                9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
            }
            current_month_name = months_map_kk.get(today.month, "Январь")
            cur.execute(
                "SELECT title, text FROM reflections "
                "WHERE month = %s ORDER BY id LIMIT 1 OFFSET %s",
                (current_month_name, today.day - 1),
            )
            row = cur.fetchone()
        else:
            cur.execute(
                "SELECT text FROM reflections_archive "
                "WHERE day = %s AND month = %s",
                (today.day, today.month),
            )
            row = cur.fetchone()

        cur.close()
        conn.close()

        if row:
            if lang == "kk":
                title_kk = row[0] or ""
                content_kk = row[1] or ""
                combined = (
                    f"{title_kk}\n\n{content_kk}"
                    if title_kk
                    else content_kk
                )
                text = format_reflection_text(combined, today, lang=lang)
            else:
                text = format_reflection_text(row[0], today, lang=lang)
            await message.answer(
                text,
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard(lang),
            )
        else:
            msg = (
                "На сегодня размышления не найдены в базе."
                if lang == "ru"
                else "Бүгінге ой-толғаулар табылмады."
            )
            await message.answer(msg, reply_markup=get_main_menu_keyboard(lang))

    except Exception as e:
        logging.error(f"Ошибка получения размышлений: {e}")
        msg = (
            "Произошла ошибка при получении размышлений."
            if lang == "ru"
            else "Ой-толғауларды алу кезінде қате орын алды."
        )
        await message.answer(msg, reply_markup=get_main_menu_keyboard(lang))


@router.message(
    F.chat.type == "private", F.text.in_({"🙏 11 Шаг", "🙏 11 Қадам"})
)
async def step_eleven_menu(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    if not lang:
        lang = "ru"
    t = TEXTS[lang]
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=t["step11_morning"],
                    callback_data="get_morning_prayer",
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t["step11_evening"],
                    callback_data="get_evening_prayer",
                )
            ],
        ]
    )
    await message.answer(
        t["step11_title"], reply_markup=keyboard, parse_mode="HTML"
    )


@router.callback_query(F.data == "get_morning_prayer")
async def send_morning_callback(callback: types.CallbackQuery):
    if callback.message.chat.type != "private":
        await callback.answer()
        return
    lang = await get_user_language(callback.from_user.id)
    if not lang:
        lang = "ru"
    text = MORNING_PRAYER_TEXT_KK if lang == "kk" else MORNING_PRAYER_TEXT_RU
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "get_evening_prayer")
async def send_evening_callback(callback: types.CallbackQuery):
    if callback.message.chat.type != "private":
        await callback.answer()
        return
    lang = await get_user_language(callback.from_user.id)
    if not lang:
        lang = "ru"
    text = EVENING_PRAYER_TEXT_KK if lang == "kk" else EVENING_PRAYER_TEXT_RU
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.message(
    F.chat.type == "private", F.text.in_({"🤝 Спонсоры", "🤝 Демеушілер"})
)
async def sponsors_menu_handler_msg(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    if not lang:
        lang = "ru"
    t = TEXTS[lang]
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=t["sponsor_brothers"],
                    callback_data="list_brothers_0",
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t["sponsor_sisters"],
                    callback_data="list_sisters_0",
                )
            ],
        ]
    )
    await message.answer(t["sponsors_title"], reply_markup=keyboard)


@router.callback_query(F.data == "menu_sponsors")
async def sponsors_menu_handler_cb(callback: types.CallbackQuery):
    if callback.message.chat.type != "private":
        await callback.answer()
        return
    lang = await get_user_language(callback.from_user.id)
    if not lang:
        lang = "ru"
    t = TEXTS[lang]
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=t["sponsor_brothers"],
                    callback_data="list_brothers_0",
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=t["sponsor_sisters"],
                    callback_data="list_sisters_0",
                )
            ],
        ]
    )
    await callback.message.edit_text(t["sponsors_title"], reply_markup=keyboard)
    await callback.answer()


@router.message(
    F.chat.type == "private", F.text.in_({"❓ Помощь", "❓ Көмек"})
)
async def help_section_handler(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    if not lang:
        lang = "ru"
    t = TEXTS[lang]
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=t["help_btn"], callback_data="call_servant"
                )
            ]
        ]
    )
    await message.answer(
        t["help_title"], reply_markup=keyboard, parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("back_to_menu"))
async def back_to_menu_callback(callback: types.CallbackQuery):
    if callback.message.chat.type != "private":
        await callback.answer()
        return
    parts = callback.data.split("_")
    lang = parts[3] if len(parts) > 3 else None

    if not lang:
        lang = await get_user_language(callback.from_user.id)
        if not lang:
            lang = "ru"

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        TEXTS[lang]["menu"],
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "call_servant")
async def call_servant_callback(callback: types.CallbackQuery):
    if callback.message.chat.type != "private":
        await callback.answer()
        return
    user = callback.from_user
    lang = await get_user_language(user.id)
    if not lang:
        lang = "ru"
    t = TEXTS[lang]
    user_link = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"
    username_text = f" (@{user.username})" if user.username else ""

    alert_text = t["servant_alert"].format(
        user_link=user_link, username_text=username_text, user_id=user.id
    )

    for servant_id in SERVANT_CHAT_IDS:
        try:
            await callback.bot.send_message(
                servant_id, alert_text, parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление служащему: {e}")

    await callback.message.answer(t["servant_success"])
    await callback.answer()