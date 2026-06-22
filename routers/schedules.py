from aiogram import Router, F
from aiogram.types import Message
from datetime import datetime

router = Router()

# Для примера. Сюда можно дописать тексты на любой день года
REFLECTIONS = {
    "01-01": "1 января. Наш первый шаг. Начнем этот год с чистого листа, доверяя Высшей Силе.",
    "06-22": "22 июня. Принятие. Сегодня я принимаю мир таким, какой он есть, и людей такими, какие они есть.",
}

@router.message(F.text == "📖 Ежедневные размышления")
async def daily_reflection(message: Message):
    today = datetime.now().strftime("%m-%d")
    text = REFLECTIONS.get(today, "📖 Ежедневное размышление: Жить только сегодняшним днем. Один день за раз, сохраняя душевный покой.")
    
    await message.answer(
        f"━━━━━━━━━━━━━━━\n"
        f"✨ РАЗМЫШЛЕНИЯ НА СЕГОДНЯ\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"{text}"
    )