from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import database as db

router = Router()

class SponsorForm(StatesGroup):
    name = State()
    age = State()
    sobriety = State()
    city = State()
    program_info = State()
    phone = State()

@router.message(F.text.in_({"🤝 Стать спонсором", "✍️ Редактировать карточку"}))
async def start_form(message: types.Message, state: FSMContext):
    existing = await db.get_sponsor_by_tg_id(message.from_user.id)
    
    if existing and message.text == "🤝 Стать спонсором":
        # Если уже спонсор, предлагаем обновиться
        kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✍️ Редактировать карточку")]], resize_keyboard=True)
        await message.answer("ℹ️ Ты уже зарегистрирован в базе спонсоров. Если твои данные (срок трезвости, опыт) изменились, нажми кнопку ниже:", reply_markup=kb)
        return

    await message.answer("🕊 **Заполнение карточки Спонсора АА**\n\n📝 **Как к тебе обращаться?** (Введи имя):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(SponsorForm.name)

@router.message(SponsorForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📅 **Сколько тебе лет?**")
    await state.set_state(SponsorForm.age)

@router.message(SponsorForm.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("🕊 **Твой актуальный срок трезвости?**\n(Например: *2 года и 3 месяца*):")
    await state.set_state(SponsorForm.sobriety)

@router.message(SponsorForm.sobriety)
async def process_sobriety(message: types.Message, state: FSMContext):
    await state.update_data(sobriety=message.text)
    await message.answer("📍 **Твой город?** (Или *Онлайн*):")
    await state.set_state(SponsorForm.city)

@router.message(SponsorForm.city)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer(
        "📖 **Твой опыт в Содружестве?**\n"
        "(Например: *Спонсирую по Большой Книге, а также делюсь опытом по 12 Традициям АА*):"
    )
    await state.set_state(SponsorForm.program_info)

@router.message(SponsorForm.program_info)
async def process_program(message: types.Message, state: FSMContext):
    await state.update_data(program_info=message.text)
    
    # Кнопка пропуска для тех, кто не хочет давать номер
    skip_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Не указывать номер (только ТГ)")]], resize_keyboard=True)
    await message.answer("📞 **Укажи свой номер телефона для связи:**\n(Или нажми кнопку ниже, чтобы оставить только ник Телеграма)", reply_markup=skip_kb)
    await state.set_state(SponsorForm.phone)

@router.message(SponsorForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    username = f"@{message.from_user.username}" if message.from_user.username else "Скрыт"
    phone_val = message.text
    
    if "Не указывать номер" in message.text:
        phone_val = "Не указан"
        if username == "Скрыт":
            await message.answer("⚠️ У тебя скрыт ник в Telegram и не указан телефон. Подопечные не смогут связаться. Пожалуйста, напиши телефон текстом:")
            return

    await state.update_data(phone=phone_val, username=username)
    data = await state.get_data()
    await state.clear()

    # Сохраняем в таблицу черновиков
    await db.save_sponsor_draft(message.from_user.id, data)

    # Показываем красивую карточку
    card_text = (
        "❤️ **Твоя карточка отправлена админам на одобрение!**\n\n"
        "✨ **КАРТОЧКА СПОНСОРА АА**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Имя:** {data['name']}\n"
        f"📅 **Возраст:** {data['age']}\n"
        f"🕊 **Трезвость:** {data['sobriety']}\n"
        f"📍 **Город:** {data['city']}\n\n"
        f"📖 **Опыт/Программа:** {data['program_info']}\n"
        f"✈️ **Telegram:** {data['username']}\n"
        f"📞 **Телефон:** {data['phone']}\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    
    # Возвращаем главное меню (предполагаем, что функция импортируется из твоего меню)
    from routers.menu import get_main_menu_keyboard
    main_kb = await get_main_menu_keyboard() 
    await message.answer(card_text, parse_mode="Markdown", reply_markup=main_kb)
    
    # Отправляем админу
    from routers.admin import send_sponsor_request_to_admin
    await send_sponsor_request_to_admin(message.bot, message.from_user.id, data)