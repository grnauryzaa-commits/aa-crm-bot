from aiogram import Router, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

def get_main_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Заполнить анкету")],
            [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard