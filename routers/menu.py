from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

# Создаем клавиатуру в одном месте
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Стать спонсором")],
        [KeyboardButton(text="🤝 Спонсоры"), KeyboardButton(text="📅 Расписание")],
        [KeyboardButton(text="❓ Помощь")]
    ],
    resize_keyboard=True
)

@router.message(Command("menu"))
async def cmd_menu(message: types.Message):
    await message.answer("Вот твое главное меню. Выбери нужный раздел:", reply_markup=main_menu)