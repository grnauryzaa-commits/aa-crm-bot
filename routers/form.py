from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from routers.states import SponsorForm # Убедись, что файл states.py существует

router = Router()

# Клавиатура отмены
cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True
)

@router.message(F.text == "❌ Отмена")
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Заполнение анкеты отменено. Вы вернулись в главное меню.", reply_markup=ReplyKeyboardRemove())

@router.message(SponsorForm.gender)
async def process_gender(message: types.Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer(
        "✨ **Принято!** ✨\n\n"
        "Теперь давай уточним важный момент для комфортного общения:\n"
        "👥 **Кого ты представляешь: Брата или Сестру?**\n"
        "(Напиши свой пол: Мужской или Женский)",
        reply_markup=cancel_kb
    )
    await state.set_state(SponsorForm.phone)

@router.message(SponsorForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена":
        return await cancel_handler(message, state)
        
    await state.update_data(phone=message.text)
    # Далее твоя логика сохранения данных...
    await message.answer("✅ **Спасибо!** Все данные сохранены.", reply_markup=ReplyKeyboardRemove())
    await state.clear()