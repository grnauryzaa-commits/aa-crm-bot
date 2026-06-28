import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import database as db
from routers.sponsors_mod import send_to_moderation

router = Router()

class SponsorForm(StatesGroup):
    name = State()
    gender = State()
    age = State()
    sobriety = State()
    city = State()
    program_info = State()
    phone = State()

@router.message(Command("start", "cancel"), FSMContext)
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    from routers.menu import get_main_menu_keyboard
    main_kb = await get_main_menu_keyboard()
    await message.answer("❌ Заполнение прервано. Возвращаемся в меню.", reply_markup=main_kb)

@router.message(F.text.in_({"➕ Стать спонсором", "✍️ Редактировать карточку"}))
async def start_form(message: types.Message, state: FSMContext):
    await message.answer("🕊 Заполнение карточки спонсора АА\n\n📝 Как к тебе обращаться? (Введи имя):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(SponsorForm.name)

@router.message(SponsorForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    gender_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🙋‍♂️ Братья"), KeyboardButton(text="🙋‍♀️ Сестры")]], resize_keyboard=True)
    await message.answer("👥 Укажи свой пол (для разделения списков):", reply_markup=gender_kb)
    await state.set_state(SponsorForm.gender)

@router.message(SponsorForm.gender, F.text.in_({"🙋‍♂️ Братья", "🙋‍♀️ Сестры"}))
async def process_gender(message: types.Message, state: FSMContext):
    # Убираем эмодзи перед сохранением
    clean_gender = message.text.replace("🙋‍♂️ ", "").replace("🙋‍♀️ ", "")
    await state.update_data(gender=clean_gender)
    await message.answer("📅 Сколько тебе лет?", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(SponsorForm.age)

@router.message(SponsorForm.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("🕊 Твой актуальный срок трезвости?")
    await state.set_state(SponsorForm.sobriety)

@router.message(SponsorForm.sobriety)
async def process_sobriety(message: types.Message, state: FSMContext):
    await state.update_data(sobriety=message.text)
    await message.answer("📍 Твой город? (Или напиши: Онлайн):")
    await state.set_state(SponsorForm.city)

@router.message(SponsorForm.city)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("📖 Твой опыт в Содружестве (Программа, Шаги, Традиции):")
    await state.set_state(SponsorForm.program_info)

@router.message(SponsorForm.program_info)
async def process_program(message: types.Message, state: FSMContext):
    await state.update_data(program_info=message.text)
    skip_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Не указывать номер (только ТГ)")]], resize_keyboard=True)
    await message.answer("📞 Укажи свой номер телефона:", reply_markup=skip_kb)
    await state.set_state(SponsorForm.phone)

@router.message(SponsorForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    username = f"@{message.from_user.username}" if message.from_user.username else "Скрыт"
    phone_val = "Не указан" if "Не указывать" in message.text else message.text
    await state.update_data(phone=phone_val, username=username)
    data = await state.get_data()
    await state.clear()
    
    age_digits = ''.join(filter(str.isdigit, str(data.get('age', '0'))))
    data['age'] = int(age_digits) if age_digits else 0
    
    await db.save_sponsor_draft(message.from_user.id, data)
    from routers.menu import get_main_menu_keyboard
    main_kb = await get_main_menu_keyboard()
    await message.answer("✅ Анкета отправлена на модерацию!", reply_markup=main_kb)
    await send_to_moderation(message.bot, message.from_user.id, data)