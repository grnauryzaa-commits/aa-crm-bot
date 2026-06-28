import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import database as db

# Импортируем нашу функцию отправки админам на модерацию
from routers.sponsors_mod import send_to_moderation

router = Router()

class SponsorForm(StatesGroup):
    name = State()
    age = State()
    sobriety = State()
    city = State()
    program_info = State()
    phone = State()

# 1. СТАРТ АНКЕТЫ (Кнопка теперь строго соответствует скриншоту)
@router.message(F.text.in_({"➕ Стать спонсором", "✍️ Редактировать карточку"}))
async def start_form(message: types.Message, state: FSMContext):
    existing = await db.get_sponsor_by_tg_id(message.from_user.id)
    
    if existing:
        kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✍️ Редактировать карточку")]], resize_keyboard=True)
        await message.answer(
            "ℹ️ Ты уже зарегистрирован в базе спонсоров.\n\n"
            "Если твои данные изменились, нажми кнопку ниже, чтобы обновить карточку:", 
            reply_markup=kb
        )
        return

    await message.answer("🕊 **Заполнение карточки Спонсора АА**\n\n📝 **Как к тебе обращаться?** (Введи имя):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(SponsorForm.name)

# 2. ИМЯ
@router.message(SponsorForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📅 **Сколько тебе лет?**")
    await state.set_state(SponsorForm.age)

# 3. ВОЗРАСТ
@router.message(SponsorForm.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("🕊 **Твой актуальный срок трезвости?**\n(Например: *2 года и 3 месяца*):")
    await state.set_state(SponsorForm.sobriety)

# 4. СРОК ТРЕЗВОСТИ
@router.message(SponsorForm.sobriety)
async def process_sobriety(message: types.Message, state: FSMContext):
    await state.update_data(sobriety=message.text)
    await message.answer("📍 **Твой город?** (Или напиши *Онлайн*):")
    await state.set_state(SponsorForm.city)

# 5. ГОРОД
@router.message(SponsorForm.city)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer(
        "📖 **Твой опыт в Содружестве?**\n"
        "(Например: *Спонсирую по Большой Книге, а также делюсь опытом по 12 Традициям АА*):"
    )
    await state.set_state(SponsorForm.program_info)

# 6. ОПЫТ В ПРОГРАММЕ
@router.message(SponsorForm.program_info)
async def process_program(message: types.Message, state: FSMContext):
    await state.update_data(program_info=message.text)
    
    skip_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Не указывать номер (только ТГ)")]], resize_keyboard=True)
    await message.answer(
        "📞 **Укажи свой номер телефона для связи:**\n"
        "(Или нажми кнопку ниже, чтобы оставить только свой аккаунт Телеграм)", 
        reply_markup=skip_kb
    )
    await state.set_state(SponsorForm.phone)

# 7. ФИНАЛ: НОМЕР ТЕЛЕФОНА И ЗАВЕРШЕНИЕ (Исправленный хэндлер)
@router.message(SponsorForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    username = f"@{message.from_user.username}" if message.from_user.username else "Скрыт"
    phone_val = message.text
    
    # Защита от зависания при нажатии кнопки скрытия номера
    if "Не указывать номер" in message.text or "только ТГ" in message.text:
        phone_val = "Не указан"
        if username == "Скрыт":
            phone_val = "Номер не указан (ТГ скрыт ⚠️)"

    await state.update_data(phone=phone_val, username=username)
    data = await state.get_data()
    await state.clear()

    # ИСПРАВЛЕНИЕ ОШИБКИ БАЗЫ ДАННЫХ:
    # Извлекаем из возраста только цифры, так как колонка age в БД имеет тип INT
    age_raw = str(data.get('age', '0'))
    age_digits = ''.join(filter(str.isdigit, age_raw))
    data['age'] = int(age_digits) if age_digits else 0

    try:
        # 1. Сохраняем анкету в таблицу черновиков (sponsor_drafts)
        await db.save_sponsor_draft(message.from_user.id, data)

        # 2. Формируем превью отправленной карточки для пользователя
        card_text = (
            "❤️ **Твоя карточка успешно отправлена админам на одобрение!**\n\n"
            "✨ **КАРТОЧКА СПОНСОРА АА**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Имя:** {data.get('name')}\n"
            f"📅 **Возраст (лет):** {data.get('age')}\n"
            f"🕊 **Трезвость:** {data.get('sobriety')}\n"
            f"📍 **Город:** {data.get('city')}\n\n"
            f"📖 **Опыт/Программа:** {data.get('program_info')}\n"
            f"✈️ **Telegram:** {data.get('username')}\n"
            f"📞 **Телефон:** {data.get('phone')}\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Пожалуйста, ожидай. Как только модератор проверит анкету, бот пришлет тебе уведомление! 🕊"
        )
        
        from routers.menu import get_main_menu_keyboard
        main_kb = await get_main_menu_keyboard() 
        await message.answer(card_text, parse_mode="Markdown", reply_markup=main_kb)
        
        # 3. Отправляем карточку с инлайн-кнопками тебе в личку на проверку
        await send_to_moderation(message.bot, message.from_user.id, data)

    except Exception as e:
        logging.error(f"Ошибка сохранения анкеты спонсора: {e}")
        from routers.menu import get_main_menu_keyboard
        main_kb = await get_main_menu_keyboard()
        await message.answer(
            f"❌ Произошла непредвиденная ошибка базы данных при сохранении.\n"
            f"Администрация уже знает об этом. Пожалуйста, попробуй позже.\n\n`Тех. лог: {e}`",
            reply_markup=main_kb
        )