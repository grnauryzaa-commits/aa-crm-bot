from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from routers.states import SponsorForm
from routers.menu import get_main_menu_keyboard
from config import ADMINS, DATABASE_URL
import database as db
import psycopg2

router = Router()

@router.message(F.text == "➕ Стать спонсором")
async def start_form(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        
    await message.answer("👤 Напиши свое имя:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SponsorForm.name)

@router.message(SponsorForm.name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) > 50:
        await message.answer("⚠️ Имя слишком длинное. Введите до 50 символов:")
        return

    await state.update_data(name=name)
    await message.answer("Какой твой пол? (Брат / Сестра)")
    await state.set_state(SponsorForm.gender)

@router.message(SponsorForm.gender)
async def process_gender(message: Message, state: FSMContext):
    gender = message.text.strip()
    if len(gender) > 20:
        await message.answer("⚠️ Слишком длинный ответ. Укажите пол (Брат / Сестра):")
        return

    await state.update_data(gender=gender)
    await message.answer("📅 Напиши свой возраст (цифрой):")
    await state.set_state(SponsorForm.age)

@router.message(SponsorForm.age)
async def process_age(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ Возраст должен состоять только из цифр. Попробуй еще раз:")
        return
        
    age = int(text)
    if age < 18 or age > 100:
        await message.answer("⚠️ Укажи реальный возраст (от 18 до 100 лет):")
        return

    await state.update_data(age=age)
    await message.answer("🕊 Какой у тебя срок трезвости? (например: 3 года 2 месяца)")
    await state.set_state(SponsorForm.sobriety)

@router.message(SponsorForm.sobriety)
async def process_sobriety(message: Message, state: FSMContext):
    sobriety = message.text.strip()
    if len(sobriety) > 100:
        await message.answer("⚠️ Слишком длинный текст. Напиши короче:")
        return

    await state.update_data(sobriety=sobriety)
    await message.answer("📍 Из какого ты города?")
    await state.set_state(SponsorForm.city)

@router.message(SponsorForm.city)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip()
    if len(city) > 50:
        await message.answer("⚠️ Название города слишком длинное:")
        return

    await state.update_data(city=city)
    await message.answer("📖 Напиши коротко о своем опыте по программе / спонсорстве:")
    await state.set_state(SponsorForm.program_info)

@router.message(SponsorForm.program_info)
async def process_program_info(message: Message, state: FSMContext):
    program_info = message.text.strip()
    if len(program_info) > 500:
        await message.answer("⚠️ Текст слишком длинный (максимум 500 символов):")
        return

    await state.update_data(program_info=program_info)
    await message.answer("📞 Напиши свой номер телефона для связи:")
    await state.set_state(SponsorForm.phone)

@router.message(SponsorForm.phone)
async def process_phone(message: Message, state: FSMContext, bot: Bot):
    phone = message.text.strip()
    if len(phone) > 50:
        await message.answer("⚠️ Слишком длинный номер:")
        return

    await state.update_data(phone=phone)
    data = await state.get_data()
    tg_id = message.from_user.id
    
    sponsor_data = {
        'name': data.get('name'),
        'gender': data.get('gender'),
        'age': data.get('age'),
        'sobriety': data.get('sobriety'),
        'city': data.get('city'),
        'program_info': data.get('program_info'),
        'username': message.from_user.username or "нет",
        'phone': phone
    }

    try:
        await db.save_sponsor_draft(tg_id, sponsor_data)
    except Exception as e:
        print(f"Ошибка сохранения черновика в БД: {e}")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить карточку", callback_data=f"approve_sp_{tg_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_sp_{tg_id}")
        ]
    ])
    
    admin_text = (
        "🔔 ЗАЯВКА НА РЕГИСТРАЦИЮ СПОНСОРА\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 Имя: {sponsor_data['name']} ({sponsor_data['gender']})\n"
        f"📅 Возраст: {sponsor_data['age']}\n"
        f"🕊 Трезвость: {sponsor_data['sobriety']}\n"
        f"📍 Город: {sponsor_data['city']}\n\n"
        f"📖 Опыт/Программа: {sponsor_data['program_info']}\n"
        f"✈️ Telegram: @{sponsor_data['username']}\n"
        f"📞 Телефон: {sponsor_data['phone']}\n"
        "━━━━━━━━━━━━━━━━━━"
    )

    for admin_id in ADMINS:
        try:
            await bot.send_message(chat_id=admin_id, text=admin_text, reply_markup=keyboard)
        except Exception as e:
            print(f"Не удалось отправить админу {admin_id}: {e}")
    
    await message.answer("✅ Твоя анкета успешно отправлена на модерацию администратору!", reply_markup=get_main_menu_keyboard())
    await state.clear()


# ==========================================
# ОБРАБОТЧИКИ КНОПОК АДМИНИСТРАТОРОВ
# ==========================================

@router.callback_query(F.data.startswith("approve_sp_"))
async def approve_sponsor(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    target_user_id = int(callback.data.split("_")[2])
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Проверяем, существует ли еще черновик (защита от повторного клика или конкуренции админов)
        cur.execute("SELECT name, gender, age, sobriety, city, username, phone, program_info FROM sponsor_drafts WHERE user_id = %s;", (target_user_id,))
        draft = cur.fetchone()
        
        if not draft:
            cur.close()
            conn.close()
            await callback.message.edit_text(f"{callback.message.text}\n\n⚠️ Эту анкету уже обработал другой администратор.", reply_markup=None)
            return

        cur.execute("""
            INSERT INTO sponsors (user_id, name, gender, age, sobriety, city, username, phone, program_info)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                name = EXCLUDED.name, gender = EXCLUDED.gender, age = EXCLUDED.age,
                sobriety = EXCLUDED.sobriety, city = EXCLUDED.city, username = EXCLUDED.username,
                phone = EXCLUDED.phone, program_info = EXCLUDED.program_info;
        """, (target_user_id, *draft))
        
        cur.execute("DELETE FROM sponsor_drafts WHERE user_id = %s;", (target_user_id,))
        conn.commit()
            
        cur.close()
        conn.close()

        await callback.message.edit_text(f"{callback.message.text}\n\n✅ ОДОБРЕНО АДМИНИСТРАТОРОМ", reply_markup=None)
        
        try:
            await bot.send_message(target_user_id, "🎉 Поздравляем! Ваша анкета спонсора одобрена.")
        except:
            pass
            
    except Exception as e:
        print(f"Ошибка в approve: {e}")
        await callback.answer("Ошибка БД", show_alert=True)

@router.callback_query(F.data.startswith("decline_sp_"))
async def decline_sponsor(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    target_user_id = int(callback.data.split("_")[2])
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("SELECT user_id FROM sponsor_drafts WHERE user_id = %s;", (target_user_id,))
        draft = cur.fetchone()
        
        if not draft:
            cur.close()
            conn.close()
            await callback.message.edit_text(f"{callback.message.text}\n\n⚠️ Эту анкету уже обработал другой администратор.", reply_markup=None)
            return

        cur.execute("DELETE FROM sponsor_drafts WHERE user_id = %s;", (target_user_id,))
        conn.commit()
        cur.close()
        conn.close()

        await callback.message.edit_text(f"{callback.message.text}\n\n❌ ОТКЛОНЕНО АДМИНИСТРАТОРОМ", reply_markup=None)
        
        try:
            await bot.send_message(target_user_id, "❌ К сожалению, ваша анкета спонсора была отклонена.")
        except:
            pass
    except Exception as e:
        print(f"Ошибка в decline: {e}")
        await callback.answer("Ошибка БД", show_alert=True)