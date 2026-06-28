from aiogram import Router, F, types

router = Router()

@router.message(F.text == "📅 Расписание")
async def show_schedule(message: types.Message):
    schedule_text = (
        "📅 РАСПИСАНИЕ ЖИВОЙ ОФФЛАЙН ГРУППЫ «НАУРЫЗ»:\n\n"
        "• Вторник: 19:00 - 20:30\n"
        "• Четверг: 19:00 - 20:30\n"
        "• Пятница: 19:00 - 20:30\n"
        "• Суббота: 19:00 - 20:30\n"
        "• Воскресенье: 15:00 - 16:30\n\n"
        "Ждем вас! Приходите вовремя, группа открыта для всех."
    )
    await message.answer(schedule_text)