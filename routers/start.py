from aiogram import Router, types
from aiogram.filters import CommandStart
# Импортируем клавиатуру из файла меню
from routers.menu import main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Добро пожаловать в бот АА Наурыз. Используй меню для навигации.", 
        reply_markup=main_menu
    )