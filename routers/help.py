from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "🆘 Мне тяжело")
async def help_handler(message: Message):
    await message.answer(
        "🤝 Ты не один. Прямо сейчас сделай глубокий вдох.\n"
        "Попробуй найти спонсора в меню, позвонить доверенному лицу или посетить онлайн-собрание.\n"
        "Главное — один день за раз. Только сегодня."
    )