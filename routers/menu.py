from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from routers.states import SponsorForm
from routers.form import get_cancel_kb # импортируем клавиатуру из form.py

router = Router()

@router.message(F.text == "Заполнить анкету")
async def start_form(message: types.Message, state: FSMContext):
    await message.answer("Начинаем заполнение.\nКакой твой пол?", reply_markup=get_cancel_kb())
    await state.set_state(SponsorForm.gender)