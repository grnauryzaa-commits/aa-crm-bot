from aiogram import Router, F, types
from aiogram.filters import Command

router = Router()

@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: types.Message):
    await message.answer("🆘 Раздел помощи. Если у вас возникли вопросы по работе бота или групп, напишите нашему администратору.")