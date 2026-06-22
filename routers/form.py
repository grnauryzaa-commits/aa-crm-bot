from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

# Состояния для анкеты
class Form(StatesGroup):
    name = State()

@router.message(F.text == "➕ Стать спонсором")
async def start_form(message: types.Message, state: FSMContext):
    await message.answer("Отлично! Вы решили стать спонсором. Как вас зовут?")
    await state.set_state(Form.name)

@router.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    user_data = await state.get_data()
    await message.answer(f"Принято, {user_data['name']}! Анкета успешно начата (здесь будет продолжение вашей логики).")
    await state.clear()