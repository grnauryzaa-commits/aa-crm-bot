from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from routers.states import SponsorForm
from routers.menu import get_main_menu_keyboard
# Импортируем функцию отправки админу из admin.py
from routers.admin import send_sponsor_request_to_admin

router = Router()

@router.message(F.text == "➕ Стать спонсором")
async def start_form(message: Message, state: FSMContext):
    await message.answer("👤 Напиши свое **имя**:", reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")
    await state.set_state(SponsorForm.name)

@router.message(SponsorForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Какой твой пол? (Брат / Сестра)")
    await state.set_state(SponsorForm.gender)

@router.message(SponsorForm.gender)
async def process_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer("📅 Напиши свой **возраст** (цифрой):", parse_mode="Markdown")
    await state.set_state(SponsorForm.age)

@router.message(SponsorForm.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("🕊 Какой у тебя **срок трезвости**? (например: 3 года 2 месяца)", parse_mode="Markdown")
    await state.set_state(SponsorForm.sobriety)

@router.message(SponsorForm.sobriety)
async def process_sobriety(message: Message, state: FSMContext):
    await state.update_data(sobriety=message.text)
    await message.answer("📍 Из какого ты **города**?", parse_mode="Markdown")
    await state.set_state(SponsorForm.city)

@router.message(SponsorForm.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("📖 Напиши коротко о своем **опыте по программе / спонсорстве**:", parse_mode="Markdown")
    await state.set_state(SponsorForm.program_info)

@router.message(SponsorForm.program_info)
async def process_program_info(message: Message, state: FSMContext):
    await state.update_data(program_info=message.text)
    await message.answer("📞 Напиши свой **номер телефона** для связи:", parse_mode="Markdown")
    await state.set_state(SponsorForm.phone)

@router.message(SponsorForm.phone)
async def process_phone(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    
    # Сохраняем черновик в базу данных, чтобы потом можно было одобрить
    import database as db
    await db.save_sponsor_draft(
        tg_id=message.from_user.id,
        name=data.get('name'),
        gender=data.get('gender'),
        age=data.get('age'),
        sobriety=data.get('sobriety'),
        city=data.get('city'),
        username=message.from_user.username or "нет",
        phone=data.get('phone'),
        program_info=data.get('program_info')
    )

    # Красивая отправка админу через функцию из admin.py
    await send_sponsor_request_to_admin(bot, message.from_user.id, data)
    
    await message.answer("✅ Твоя анкета успешно отправлена на модерацию администратору!", reply_markup=get_main_menu_keyboard())
    await state.clear()