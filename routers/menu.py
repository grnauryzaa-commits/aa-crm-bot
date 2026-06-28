from aiogram import Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

def get_main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📖 Ежедневные размышления")],
            [KeyboardButton(text="➕ Стать спонсором")],
            [KeyboardButton(text="🤝 Спонсоры"), KeyboardButton(text="📅 Расписание")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )