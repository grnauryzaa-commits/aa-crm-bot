from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states import SponsorForm
from storage import pending_forms
from config import ADMIN_IDS

router = Router()


# 🚀 СТАРТ АНКЕТЫ
@router.message(F.text == "➕ Стать спонсором")
async def start_form(message: Message, state: FSMContext):

    await state.set_state(SponsorForm.name)

    await message.answer(
        "👤 <b>Шаг 1/9</b>\n\n"
        "Как тебя зовут?\n\n"
        "👉 Напиши своё имя (как к тебе обращаться в программе)"
    )


# 🎂 2. ВОЗРАСТ
@router.message(SponsorForm.name)
async def step_name(message: Message, state: FSMContext):

    await state.update_data(name=message.text)
    await state.set_state(SponsorForm.age)

    await message.answer(
        "🎂 <b>Шаг 2/9</b>\n\n"
        "Сколько тебе лет?\n\n"
        "👉 Укажи реальный возраст"
    )


# 🧠 3. ИДЕНТИФИКАЦИЯ
@router.message(SponsorForm.age)
async def step_age(message: Message, state: FSMContext):

    await state.update_data(age=message.text)
    await state.set_state(SponsorForm.identity)

    await message.answer(
        "🧠 <b>Шаг 3/9</b>\n\n"
        "С чем ты пришёл в программу?\n\n"
        "👉 Например: алкоголизм, зависимость, созависимость"
    )


# ⏳ 4. ТРЕЗВОСТЬ
@router.message(SponsorForm.identity)
async def step_identity(message: Message, state: FSMContext):

    await state.update_data(identity=message.text)
    await state.set_state(SponsorForm.sobriety)

    await message.answer(
        "⏳ <b>Шаг 4/9</b>\n\n"
        "Какой у тебя срок трезвости?\n\n"
        "👉 Например: 2 месяца, 1 год, 5 лет"
    )


# 🏙 5. ГОРОД
@router.message(SponsorForm.sobriety)
async def step_sobriety(message: Message, state: FSMContext):

    await state.update_data(sobriety=message.text)
    await state.set_state(SponsorForm.city)

    await message.answer(
        "🏙 <b>Шаг 5/9</b>\n\n"
        "В каком городе ты находишься?\n\n"
        "👉 Это важно для подбора спонсора"
    )


# 📚 6. ФОРМАТ
@router.message(SponsorForm.city)
async def step_city(message: Message, state: FSMContext):

    await state.update_data(city=message.text)
    await state.set_state(SponsorForm.formats)

    await message.answer(
        "📚 <b>Шаг 6/9</b>\n\n"
        "Какой формат работы тебе нужен?\n\n"
        "👉 шаги / традиции / оба / онлайн / офлайн"
    )


# 📱 7. TELEGRAM
@router.message(SponsorForm.formats)
async def step_formats(message: Message, state: FSMContext):

    await state.update_data(formats=message.text)
    await state.set_state(SponsorForm.telegram)

    await message.answer(
        "📱 <b>Шаг 7/9</b>\n\n"
        "Укажи свой Telegram\n\n"
        "👉 пример: @username"
    )


# ☎️ 8. ТЕЛЕФОН
@router.message(SponsorForm.telegram)
async def step_telegram(message: Message, state: FSMContext):

    await state.update_data(telegram=message.text)
    await state.set_state(SponsorForm.phone)

    await message.answer(
        "☎️ <b>Шаг 8/9</b>\n\n"
        "Укажи номер телефона\n\n"
        "👉 только для связи со спонсором"
    )


# 📌 9. О СЕБЕ
@router.message(SponsorForm.phone)
async def step_phone(message: Message, state: FSMContext):

    await state.update_data(phone=message.text)
    await state.set_state(SponsorForm.about)

    await message.answer(
        "📌 <b>Шаг 9/9</b>\n\n"
        "Расскажи немного о себе\n\n"
        "👉 Как пришёл в программу, что сейчас важно"
    )


# 🧾 ФИНАЛ → МОДЕРАЦИЯ
@router.message(SponsorForm.about)
async def final_step(message: Message, state: FSMContext, bot: Bot):

    data = await state.get_data()
    data["about"] = message.text

    uid = message.from_user.id

    # 💾 в очередь модерации
    pending_forms[uid] = data

    text = (
        "📥 <b>НОВАЯ ЗАЯВКА НА СПОНСОРА</b>\n\n"
        f"👤 {data['name']}\n"
        f"🎂 {data['age']}\n"
        f"🧠 {data['identity']}\n"
        f"⏳ {data['sobriety']}\n"
        f"🏙 {data['city']}\n"
        f"📚 {data['formats']}\n\n"
        f"📱 {data['telegram']}\n"
        f"☎️ {data['phone']}\n\n"
        f"📌 {data['about']}"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Принять", callback_data=f"ok_{uid}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"no_{uid}")
    ]])

    for admin in ADMIN_IDS:
        await bot.send_message(admin, text, reply_markup=kb)

    await message.answer(
        "📩 <b>Заявка отправлена на модерацию</b>\n\n"
        "Ожидай решения администратора 🙏"
    )

    await state.clear()