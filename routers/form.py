from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from routers.states import SponsorForm

router = Router()

def get_cancel_kb():
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True, one_time_keyboard=True
    )

@router.message(F.text == "❌ Отмена")
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Заполнение отменено.", reply_markup=types.ReplyKeyboardRemove())

@router.message(SponsorForm.gender)
async def process_gender(message: types.Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer(
        "✨ **Принято!** ✨\n\n"
        "👥 **Брат или Сестра?**\n"
        "(Напиши: Мужской или Женский)",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(SponsorForm.phone)

@router.message(SponsorForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    # Тут можно сохранить данные в БД
    await message.answer("✅ **Спасибо!** Все данные сохранены.", reply_markup=types.ReplyKeyboardRemove())
    await state.clear()