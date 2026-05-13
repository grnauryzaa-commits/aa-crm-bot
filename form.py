from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from database import add_sponsor
from config import ADMIN_IDS


router = Router()


# =====================================================
# FSM STATES
# =====================================================

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


# =====================================================
# START FORM
# =====================================================

@router.message(F.text == "➕ Стать спонсором")
async def start_form(message: Message, state: FSMContext):

    await state.set_state(SponsorForm.name)

    await message.answer(
        "━━━━━━━━━━━━━━━\n"
        "🤝 АНКЕТА СПОНСОРА\n"
        "━━━━━━━━━━━━━━━\n\n"
        "👤 Как тебя зовут?\n\n"
        "Напиши имя или как к тебе обращаться."
    )


# =====================================================
# NAME
# =====================================================

@router.message(SponsorForm.name)
async def form_name(message: Message, state: FSMContext):

    await state.update_data(name=message.text)

    await state.set_state(SponsorForm.age)

    await message.answer(
        "🎂 Сколько тебе лет?"
    )


# =====================================================
# AGE
# =====================================================

@router.message(SponsorForm.age)
async def form_age(message: Message, state: FSMContext):

    await state.update_data(age=message.text)

    await state.set_state(SponsorForm.identity)

    await message.answer(
        "🧠 Какая у тебя идентификация?\n\n"
        "Например:\n"
        "• алкоголик\n"
        "• зависимый\n"
        "• химически зависимый"
    )


# =====================================================
# IDENTITY
# =====================================================

@router.message(SponsorForm.identity)
async def form_identity(message: Message, state: FSMContext):

    await state.update_data(identity=message.text)

    await state.set_state(SponsorForm.sobriety)

    await message.answer(
        "⏳ Какой у тебя срок трезвости?"
    )


# =====================================================
# SOBRIETY
# =====================================================

@router.message(SponsorForm.sobriety)
async def form_sobriety(message: Message, state: FSMContext):

    await state.update_data(sobriety=message.text)

    await state.set_state(SponsorForm.city)

    await message.answer(
        "🏙 В каком ты городе?"
    )


# =====================================================
# CITY
# =====================================================

@router.message(SponsorForm.city)
async def form_city(message: Message, state: FSMContext):

    await state.update_data(city=message.text)

    await state.set_state(SponsorForm.formats)

    await message.answer(
        "📚 Какой формат спонсорства ты проводишь?\n\n"
        "Например:\n"
        "• Онлайн\n"
        "• Оффлайн\n"
        "• По шагам\n"
        "• По традициям"
    )


# =====================================================
# FORMATS
# =====================================================

@router.message(SponsorForm.formats)
async def form_formats(message: Message, state: FSMContext):

    await state.update_data(formats=message.text)

    await state.set_state(SponsorForm.telegram)

    await message.answer(
        "📱 Напиши свой Telegram username\n\n"
        "Например:\n"
        "@username"
    )


# =====================================================
# TELEGRAM
# =====================================================

@router.message(SponsorForm.telegram)
async def form_telegram(message: Message, state: FSMContext):

    await state.update_data(telegram=message.text)

    await state.set_state(SponsorForm.phone)

    await message.answer(
        "☎️ Оставь номер телефона\n\n"
        "Или напиши:\n"
        "Без телефона"
    )


# =====================================================
# PHONE
# =====================================================

@router.message(SponsorForm.phone)
async def form_phone(message: Message, state: FSMContext):

    await state.update_data(phone=message.text)

    await state.set_state(SponsorForm.about)

    await message.answer(
        "📌 Расскажи немного о себе:\n\n"
        "• опыт программы\n"
        "• как проходишь шаги\n"
        "• чем можешь быть полезен"
    )


# =====================================================
# ABOUT
# =====================================================

@router.message(SponsorForm.about)
async def form_about(message: Message, state: FSMContext, bot: Bot):

    await state.update_data(about=message.text)

    data = await state.get_data()

    add_sponsor((
        data["name"],
        data["age"],
        data["identity"],
        data["sobriety"],
        data["city"],
        data["formats"],
        data["telegram"],
        data["phone"],
        data["about"]
    ))

    text = (
        "━━━━━━━━━━━━━━━\n"
        "📥 НОВАЯ ЗАЯВКА\n"
        "━━━━━━━━━━━━━━━\n\n"

        f"👤 Имя: {data['name']}\n"
        f"🎂 Возраст: {data['age']}\n"
        f"🧠 Идентификация: {data['identity']}\n"
        f"⏳ Трезвость: {data['sobriety']}\n"
        f"🏙 Город: {data['city']}\n"
        f"📚 Формат: {data['formats']}\n\n"

        f"📱 Telegram: {data['telegram']}\n"
        f"☎️ Телефон: {data['phone']}\n\n"

        f"📌 О себе:\n{data['about']}"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять",
                    callback_data="approve"
                ),

                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data="decline"
                )
            ]
        ]
    )

    for admin in ADMIN_IDS:

        await bot.send_message(
            admin,
            text,
            reply_markup=kb
        )

    await message.answer(
        "━━━━━━━━━━━━━━━\n"
        "✅ ЗАЯВКА ОТПРАВЛЕНА\n"
        "━━━━━━━━━━━━━━━\n\n"
        "Спасибо 🙏\n"
        "После проверки администрацией\n"
        "ты появишься в списке спонсоров."
    )

    await state.clear()