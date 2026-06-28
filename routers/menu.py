from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

async def get_main_menu_keyboard():
    # ИСПРАВЛЕНО: Кнопки прописаны строго так, как они отображаются на телефоне
    keyboard = [
        [KeyboardButton(text="📘 Ежедневные размышления")],
        [KeyboardButton(text="➕ Стать спонсором")],
        [KeyboardButton(text="🤝 Спонсоры"), KeyboardButton(text="📅 Расписание группы")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Хэндлер вызова меню, если человек пишет что-то абстрактное
@router.message(F.text == "💻 Главное меню")
async def show_menu(message: types.Message):
    kb = await get_main_menu_keyboard()
    await message.answer("Вы вернулись в главное меню. Выберите интересующий раздел:", reply_markup=kb)