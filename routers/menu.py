from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import psycopg2
from datetime import datetime
import html
import logging
from routers.reflections import MORNING_PRAYER_TEXT, EVENING_PRAYER_TEXT

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
        resize_keyboard=True
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
            await message.answer(text, parse_mode="HTML")
        else:
            await message.answer("На сегодня размышления не найдены в базе.")
    except Exception as e:
        logging.error(f"Ошибка получения размышлений для пользователя: {e}")
        await message.answer("Произошла ошибка при получении размышлений.")

# Обработка кнопки "🙏 11 Шаг" (вызов инлайн-меню с молитвами)
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

# Обработка кнопки "➕ Стать спонсором"
@router.message(F.text == "➕ Стать спонсором")
async def become_sponsor_handler(message: types.Message):
    await message.answer(
        "➕ <b>Стать спонсором</b>\n\n"
        "Спонсорство в АА — это передача своего опыта выздоровления другим.\n"
        "Чтобы зарегистрироваться как спонсор, пожалуйста, укажи свои данные или свяжись с ответственным.",
        parse_mode="HTML"
    )

# Обработка инлайн-кнопки утренней молитвы
@router.callback_query(F.data == "get_morning_prayer")
async def send_morning_callback(callback: types.CallbackQuery):
    await callback.message.answer(MORNING_PRAYER_TEXT, parse_mode="HTML")
    await callback.answer()

# Обработка инлайн-кнопки вечерней молитвы
@router.callback_query(F.data == "get_evening_prayer")
async def send_evening_callback(callback: types.CallbackQuery):
    await callback.message.answer(EVENING_PRAYER_TEXT, parse_mode="HTML")
    await callback.answer()