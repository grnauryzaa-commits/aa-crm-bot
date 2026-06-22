from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# 1. Создаем роутер
router = Router()

# 2. Создаем клавиатуру главного меню (которую ищет start.py)
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Стать спонсором")],
        [KeyboardButton(text="🤝 Спонсоры"), KeyboardButton(text="📅 Расписание")],
        [KeyboardButton(text="❓ Помощь")]
    ],
    resize_keyboard=True
)

# 3. Хэндлер на команду /menu
@router.message(Command("menu"))
async def cmd_menu(message: types.Message):
    await message.answer("Вот твое главное меню:", reply_markup=main_menu)