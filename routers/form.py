from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from routers.states import SponsorForm
from routers.menu import get_main_menu_keyboard
from config import ADMINS

router = Router()

@router.message(F.text == "➕ Стать спонсором")
async def start_form(message: Message, state: FSMContext):
    await message.answer("Какой твой пол? (Брат/Сестра)", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SponsorForm.gender)

@router.message(SponsorForm.gender)
async def process_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer("Принято. Напиши номер телефона:")
    await state.set_state(SponsorForm.phone)

@router.message(SponsorForm.phone)
async def process_phone(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    # Отправка админу
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, f"Новая анкета:\nПол: {data.get('gender')}\nТел: {message.text}\nUser: @{message.from_user.username}")
        except:
            pass # Если админ не в сети
    
    await message.answer("✅ Анкета отправлена!", reply_markup=get_main_menu_keyboard())
    await state.clear() # ЭТО КЛЮЧЕВАЯ СТРОКА: Бот больше не зависнет