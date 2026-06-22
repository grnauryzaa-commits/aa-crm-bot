from aiogram import Router, F, types

router = Router()

@router.message(F.text == "📅 Расписание")
async def show_schedule(message: types.Message):
    schedule_text = (
        "📅 **Расписание живой оффлайн группы «Наурыз»**:\n\n"
        "• Вторник: 19:00\n"
        "• Четверг: 19:00\n"
        "• Пятница: 19:00\n"
        "• Суббота: 19:00\n"
        "• Воскресенье: 15:00\n\n"
        "Ждем вас! Приходите вовремя."
    )
    await message.answer(schedule_text, parse_mode="Markdown")