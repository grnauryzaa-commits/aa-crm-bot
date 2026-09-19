from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_user_language
from config import SERVANT_CHAT_IDS
import psycopg2
from config import DATABASE_URL
import logging

router = Router()

class SponsorForm(StatesGroup):
    name = State()
    city = State()
    sobriety_date = State()
    sponsor_name = State()
    phone = State()
    comment = State()

FORM_TEXTS = {
    "ru": {
        "q_name": "👤 <b>Напиши свое имя:</b>",
        "q_city": "📍 <b>В каком городе ты находишься?</b>",
        "q_sobriety": "📅 <b>Укажи дату своей трезвости</b> (например, <i>15.05.2020</i> или просто год):",
        "q_sponsor": "🤝 <b>Кто твой спонсор?</b> (Имя, Фамилия):",
        "q_phone": "📱 <b>Укажи свой номер телефона</b> (для связи в WhatsApp/Telegram):",
        "q_comment": "💬 <b>Напиши пару слов о себе</b> или оставь прочерк (-):",
        "error_text": "❌ Пожалуйста, отправляйте текст, а не медиафайлы.",
        "success": (
            "✅ <b>Спасибо! Ваша анкета успешно заполнена и отправлена на модерацию.</b>\n\n"
            "Как только администратор проверит данные, ваш контакт появится в списке спонсоров."
        ),
        "admin_alert": (
            "🚨 <b>Новая анкета спонсора!</b>\n\n"
            "👤 <b>Имя:</b> {name}\n"
            "📍 <b>Город:</b> {city}\n"
            "📅 <b>Трезвость:</b> {sobriety}\n"
            "🤝 <b>Спонсор:</b> {sponsor}\n"
            "📱 <b>Телефон:</b> {phone}\n"
            "💬 <b>О себе:</b> {comment}\n"
            "🆔 <b>Telegram ID:</b> <code>{user_id}</code>"
        )
    },
    "kk": {
        "q_name": "👤 <b>Атыңызды жазыңыз:</b>",
        "q_city": "📍 <b>Қай қалада тұрасыз?</b>",
        "q_sobriety": "📅 <b>Сауығу күнін немесе жылын жазыңыз</b> (мысалы: <i>15.05.2020</i> немесе тек жыл):",
        "q_sponsor": "🤝 <b>Демеушіңіз кім?</b> (Аты, Тегі):",
        "q_phone": "📱 <b>Байланыс телефоныңызды жазыңыз</b> (WhatsApp/Telegram үшін):",
        "q_comment": "💬 <b>Өзіңіз туралы қысқаша жазыңыз</b> немесе сызықша (-) қойыңыз:",
        "error_text": "❌ Медиафайлдар емес, мәтін жіберуіңізді сұраймыз.",
        "success": (
            "✅ <b>Рақмет! Сіздің сауалнаңыз сәтті толтырылып, тексеруге жіберілді.</b>\n\n"
            "Әкімші деректерді тексергеннен кейін, сіздің байланысыңыз демеушілер тізімінде пайда болады."
        ),
        "admin_alert": (
            "🚨 <b>Жаңа демеуші сауалнамасы!</b>\n\n"
            "👤 <b>Аты:</b> {name}\n"
            "📍 <b>Қала:</b> {city}\n"
            "📅 <b>Сауығу күні:</b> {sobriety}\n"
            "🤝 <b>Демеушісі:</b> {sponsor}\n"
            "📱 <b>Телефон:</b> {phone}\n"
            "💬 <b>Өзі туралы:</b> {comment}\n"
            "🆔 <b>Telegram ID:</b> <code>{user_id}</code>"
        )
    }
}

def save_sponsor_to_db(user_id, name, city, sobriety_date, sponsor_name, phone, comment):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO sponsors (user_id, name, city, sobriety_date, sponsor_name, phone, comment)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                name = EXCLUDED.name,
                city = EXCLUDED.city,
                sobriety_date = EXCLUDED.sobriety_date,
                sponsor_name = EXCLUDED.sponsor_name,
                phone = EXCLUDED.phone,
                comment = EXCLUDED.comment
            """,
            (user_id, name, city, sobriety_date, sponsor_name, phone, comment)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Ошибка сохранения спонсора в базу: {e}")

@router.callback_query(F.data == "start_sponsor_registration")
async def start_sponsor_form(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    # Принудительная проверка: если кнопка была на казахском, гарантированно ставим 'kk'
    if callback.message.reply_markup:
        for row in callback.message.reply_markup.inline_keyboard:
            for btn in row:
                if btn.callback_data == "start_sponsor_registration" and "толтыру" in btn.text.lower():
                    lang = "kk"

    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
    
    await state.set_state(SponsorForm.name)
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(t["q_name"], parse_mode="HTML")
    await callback.answer()

@router.message(SponsorForm.name, F.text)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(SponsorForm.city)
    lang = await get_user_language(message.from_user.id)
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
    await message.answer(t["q_city"], parse_mode="HTML")

@router.message(SponsorForm.name)
async def process_name_invalid(message: Message):
    lang = await get_user_language(message.from_user.id)
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
    await message.answer(t["error_text"])

@router.message(SponsorForm.city, F.text)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(SponsorForm.sobriety_date)
    lang = await get_user_language(message.from_user.id)
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
    await message.answer(t["q_sobriety"], parse_mode="HTML")

@router.message(SponsorForm.city)
async def process_city_invalid(message: Message):
    lang = await get_user_language(message.from_user.id)
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
    await message.answer(t["error_text"])

@router.message(SponsorForm.sobriety_date, F.text)
async def process_sobriety(message: Message, state: FSMContext):
    await state.update_data(sobriety_date=message.text)
    await state.set_state(SponsorForm.sponsor_name)
    lang = await get_user_language(message.from_user.id)
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
    await message.answer(t["q_sponsor"], parse_mode="HTML")

@router.message(SponsorForm.sobriety_date)
async def process_sobriety_invalid(message: Message):
    lang = await get_user_language(message.from_user.id)
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
    await message.answer(t["error_text"])

@router.message(SponsorForm.sponsor_name, F.text)
async def process_sponsor_name(message: Message, state: FSMContext):
    await state.update_data(sponsor_name=message.text)
    await state.set_state(SponsorForm.phone)
    lang = await get_user_language(message.from_user.id)
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
    await message.answer(t["q_phone"], parse_mode="HTML")

@router.message(SponsorForm.sponsor_name)
async def process_sponsor_invalid(message: Message):
    lang = await get_user_language(message.from_user.id)
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
    await message.answer(t["error_text"])

@router.message(SponsorForm.phone, F.text)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(SponsorForm.comment)
    lang = await get_user_language(message.from_user.id)
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
    await message.answer(t["q_comment"], parse_mode="HTML")

@router.message(SponsorForm.phone)
async def process_phone_invalid(message: Message):
    lang = await get_user_language(message.from_user.id)
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
    await message.answer(t["error_text"])

@router.message(SponsorForm.comment, F.text)
async def process_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    data = await state.get_data()
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

    save_sponsor_to_db(
        user_id=user_id,
        name=data["name"],
        city=data["city"],
        sobriety_date=data["sobriety_date"],
        sponsor_name=data["sponsor_name"],
        phone=data["phone"],
        comment=data["comment"]
    )

    await message.answer(t["success"], parse_mode="HTML")

    admin_text = t["admin_alert"].format(
        name=data["name"],
        city=data["city"],
        sobriety=data["sobriety_date"],
        sponsor=data["sponsor_name"],
        phone=data["phone"],
        comment=data["comment"],
        user_id=user_id
    )

    for servant_id in SERVANT_CHAT_IDS:
        try:
            await message.bot.send_message(chat_id=servant_id, text=admin_text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление о новой анкете служащему {servant_id}: {e}")

    await state.clear()

@router.message(SponsorForm.comment)
async def process_comment_invalid(message: Message):
    lang = await get_user_language(message.from_user.id)
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
    await message.answer(t["error_text"])