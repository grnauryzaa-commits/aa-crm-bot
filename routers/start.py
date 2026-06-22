from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from routers.menu import main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет 🙏 Добро пожаловать в бот взаимопомощи.\n"
        "Здесь ты можешь найти спонсора или оставить свою заявку.",
        reply_markup=main_menu
    )