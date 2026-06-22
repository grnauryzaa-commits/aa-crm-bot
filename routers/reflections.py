from aiogram import Router, F, types
from datetime import datetime

router = Router()

@router.message(F.text == "📘 Ежедневные размышления")
async def show_reflections(message: types.Message):
    now = datetime.now()
    day = now.strftime("%d")
    month = now.strftime("%m")
    
    # Ссылка на официальный календарь размышлений АА
    url = f"https://aarussia.ru/daily-reflections/?date={day}-{month}"
    
    text = (
        "📘 **Ежедневные размышления АА**\n\n"
        "Каждый день — это новый шаг на пути выздоровления. Прочесть сегодняшнее размышление можно на официальном сайте по ссылке ниже:\n\n"
        f"🔗 [Читать размышление на сегодня]({url})"
    )
    
    await message.answer(text, parse_mode="Markdown")