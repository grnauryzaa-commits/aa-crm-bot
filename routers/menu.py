from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import psycopg2
from datetime import datetime
import html
import logging
from routers.reflections import MORNING_PRAYER_TEXT, EVENING_PRAYER_TEXT
from routers.ai_helper import ask_ai_for_beginner

router = Router()

DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"

def get_main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📖 Ежедневные размышления")],
            [KeyboardButton(text="🙏 11 Шаг"), KeyboardButton(text="➕ Стать спонсором")],
            [KeyboardButton(text="🤝 Спонсоры"), KeyboardButton(text="📅 Расписание")],
            [KeyboardButton(text="❓ Помощь")]
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
async def cmd_start(message: types.Message):
    await message.answer(
        "Приветствую! Добро пожаловать в бот сообщества Анонимных Алкоголиков.\n\n"
        "🤖 Вы можете задать мне любой вопрос о программе АА своими словами, и я постараюсь помочь.\n\n"
        "👇 <b>Главное меню всегда находится внизу экрана.</b> Нажимайте на нужные кнопки:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "📖 Ежедневные размышления")
async def show_daily_reflection(message: types.Message):
    today = datetime.now()
    try:
        conn = psycopg2.connect(DB_URL)
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
        logging.error(f"Ошибка получения размышлений для пользователя: {e}")
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

# Обработчик кнопки "Стать спонсором" с кнопкой "Назад"
@router.message(F.text == "➕ Стать спонсором")
async def become_sponsors_menu(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
        ]
    )
    await message.answer(
        "➕ <b>Стать спонсором в АА</b>\n\n"
        "Спонсор — это человек, который прошел Шаги и готов делиться опытом с другими. "
        "Если вы чувствуете в себе силы и имеете устойчивую трезвость, вы можете зарегистрироваться как спонсор.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(callback: types.CallbackQuery):
    # Удаляем сообщение с текстом раздела, чтобы не засорять чат
    await callback.message.delete()
    await callback.answer("Возврат в меню")

# Обработчик вызова живого служащего
@router.callback_query(F.data == "call_servant")
async def call_servant_callback(callback: types.CallbackQuery):
    await callback.message.answer(
        "🙏 Ваша заявка принята. Дежурный служащий сообщества свяжется с вами в ближайшее время.\n\n"
        "Также вы всегда можете обратиться к разделу «Расписание» или на живые группы."
    )
    await callback.answer()

# Обработчик всех остальных текстовых сообщений (вопросы к ИИ)
@router.message(F.text)
async def handle_beginner_questions(message: types.Message):
    menu_buttons = [
        "📖 Ежедневные размышления", "🙏 11 Шаг", 
        "➕ Стать спонсором", "🤝 Спонсоры", 
        "📅 Расписание", "❓ Помощь"
    ]
    if message.text in menu_buttons:
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    ai_response = await ask_ai_for_beginner(message.text)

    servant_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Позвать живого служащего", callback_data="call_servant")]
        ]
    )

    await message.answer(
        ai_response, 
        parse_mode="Markdown", 
        reply_markup=servant_keyboard
    )