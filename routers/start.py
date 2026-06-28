import logging
from aiogram import Router, types
from aiogram.filters import Command
from routers.menu import get_main_menu_keyboard

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    logging.info(f"Пользователь {message.from_user.id} нажал /start")
    
    welcome_text = (
        "🕊 **Добро пожаловать в телеграм-бот группы АА «Наурыз»!**\n\n"
        "Этот бот создан для поддержки участников нашего Содружества.\n"
        "Здесь ты можешь узнать актуальное расписание живых встреч, найти спонсора "
        "или предложить свою помощь в качестве наставника.\n\n"
        "Пожалуйста, выбери интересующий раздел в меню ниже 👇"
    )
    
    kb = await get_main_menu_keyboard()
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=kb)