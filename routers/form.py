from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from storage import pending_forms
from config import ADMIN_IDS

router = Router()

class SponsorForm(StatesGroup):
    name = State()
    age = State()
    identity = State()
    sobriety = State()
    city = State()
    formats = State()
    telegram = State()
    phone = State()
    about = State()

@router.message(F.text == "➕ Стать спонсором")
async def start_form(message: Message, state: FSMContext):
    await state.set_state(SponsorForm.name)
    await message.answer(
        "━━━━━━━━━━━━━━━\n🤝 АНКЕТА СПОНСОРА\n━━━━━━━━━━━━━━━\n\n👤 Как тебя зовут?\nНапиши имя."
    )

@router.message(SponsorForm.name)
async def form_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(SponsorForm.age)
    await message.answer("🎂 Сколько тебе лет?")

@router.message(SponsorForm.age)
async def form_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(SponsorForm.identity)
    await message.answer("🧠 Какая у тебя идентификация?\n(например: алкоголик, зависимый)")

@router.message(SponsorForm.identity)
async def form_identity(message: Message, state: FSMContext):
    await state.update_data(identity=message.text)
    await state.set_state(SponsorForm.sobriety)
    await message.answer("⏳ Какой у тебя срок трезвости?")

@router.message(SponsorForm.sobriety)
async def form_sobriety(message: Message, state: FSMContext):
    await state.update_data(sobriety=message.text)
    await state.set_state(SponsorForm.city)
    await message.answer("🏙 В каком ты городе?")

@router.message(SponsorForm.city)
async def form_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(SponsorForm.formats)
    await message.answer("📚 Формат спонсорства?\n(Онлайн, Оффлайн, по Шагам)")

@router.message(SponsorForm.formats)
async def form_formats(message: Message, state: FSMContext):
    await state.update_data(formats=message.text)
    await state.set_state(SponsorForm.telegram)
    await message.answer("📱 Напиши свой Telegram username (с @ или ссылку)")

@router.message(SponsorForm.telegram)
async def form_telegram(message: Message, state: FSMContext):
    tg = message.text if message.text.startswith("@") else f"@{message.text}"
    await state.update_data(telegram=tg)
    await state.set_state(SponsorForm.phone)
    await message.answer("☎️ Номер телефона (или напиши 'Без телефона')")

@router.message(SponsorForm.phone)
async def form_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(SponsorForm.about)
    await message.answer("📌 Расскажи о себе (опыт в программе, шаги):")

@router.message(SponsorForm.about)
async def form_about(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(about=message.text)
    data = await state.get_data()
    uid = message.from_user.id

    # Сохраняем временно в ОЗУ
    pending_forms[uid] = data

    text = (
        "━━━━━━━━━━━━━━━\n📥 НОВАЯ ЗАЯВКА\n━━━━━━━━━━━━━━━\n\n"
        f"👤 Имя: {data['name']}\n🎂 Возраст: {data['age']}\n"
        f"🧠 Идентификация: {data['identity']}\n⏳ Трезвость: {data['sobriety']}\n"
        f"🏙 Город: {data['city']}\n📚 Формат: {data['formats']}\n"
        f"📱 TG: {data['telegram']}\n☎️ Тел: {data['phone']}\n\n"
        f"📌 О себе:\n{data['about']}"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"ok_{uid}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"no_{uid}")
            ]
        ]
    )

    for admin in ADMIN_IDS:
        try:
            await bot.send_message(admin, text, reply_markup=kb)
        except Exception:
            pass

    await message.answer("✅ Заявка отправлена администрации на модерацию. Спасибо!")
    await state.clear()