from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text.contains("тяжело"))
async def help(message: Message):
    await message.answer("🤝 Ты не один. Дыши. Один день за раз.")