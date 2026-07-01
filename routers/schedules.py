from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Функция клавиатуры
def get_schedules_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Онлайн группы", callback_data="sched_online")],
        [InlineKeyboardButton(text="🏢 Группы Алматы", callback_data="sched_alm")],
        [InlineKeyboardButton(text="Закрыть", callback_data="sched_close")]
    ])
    return keyboard

@router.message(F.text == "📅 Расписание собраний")
async def show_schedules(message: types.Message):
    await message.answer("Выберите направление:", reply_markup=get_schedules_kb())

@router.callback_query(F.data.startswith("sched_"))
async def callback_schedules(callback: types.CallbackQuery):
    if callback.data == "sched_online":
        await callback.message.edit_text("🌐 <b>Онлайн:</b>\n\nПробуждение: Вт, Чт, Сб 21:00\nБірлік: Чт 21:00", 
                                         reply_markup=get_schedules_kb(), parse_mode="HTML")
    elif callback.data == "sched_alm":
        await callback.message.edit_text("🏢 <b>Алматы:</b>\n\nВиктория: Жубанова 3а\n8 марта: Зенкова 24", 
                                         reply_markup=get_schedules_kb(), parse_mode="HTML")
    elif callback.data == "sched_close":
        await callback.message.delete()
    await callback.answer()