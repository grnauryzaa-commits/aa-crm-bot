from aiogram import Router, types
from aiogram.filters import Command

# Создаем роутер, который ищет bot.py
router = Router()

@router.message(Command("menu"))
async def cmd_menu(message: types.Message):
    await message.answer("Вот твое главное меню. Выбери нужное действие:")