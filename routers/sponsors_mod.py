import logging
import psycopg2
from aiogram import Router, F, Bot, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import DATABASE_URL as DB_URL

# 🔴 ВАЖНО: Прямо здесь укажи свой точный Telegram ID, чтобы карточки шли тебе!
ADMIN_ID = 7374545230 

router = Router()

async def send_to_moderation(bot: Bot, user_id: int, data: dict):
    """Функция отправляет карточку на модерацию администратору"""
    moderation_text = (
        "🔔 ПОСТУПИЛА НОВАЯ АНКЕТА СПОНСОРА!\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 Имя: {data.get('name')}\n"
        f"📅 Возраст: {data.get('age')} лет\n"
        f"🕊 Трезвость: {data.get('sobriety')}\n"
        f"📍 Город: {data.get('city')}\n\n"
        f"📖 Опыт/Программа: {data.get('program_info')}\n"
        f"✈️ Telegram: {data.get('username')}\n"
        f"📞 Телефон: {data.get('phone')}\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    
    # Кнопки для админа
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"mod_approve:{user_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mod_reject:{user_id}")
        ]
    ])
    
    try:
        # Отправляем именно на твой ID
        await bot.send_message(chat_id=ADMIN_ID, text=moderation_text, reply_markup=kb)
        logging.info(f"Анкета пользователя {user_id} успешно отправлена админу {ADMIN_ID}")
    except Exception as e:
        logging.error(f"Не удалось отправить анкету админу: {e}")


# ОБРАБОТКА НАЖАТИЯ КНОПКИ "ОДОБРИТЬ"
@router.callback_query(F.data.startswith("mod_approve:"))
async def approve_sponsor(callback: types.CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Переносим из черновиков в активные спонсоры
        cur.execute("""
            INSERT INTO sponsors (user_id, name, age, sobriety, city, username, phone, program_info)
            SELECT user_id, name, age, sobriety, city, username, phone, program_info 
            FROM sponsor_drafts WHERE user_id = %s
            ON CONFLICT (user_id) DO UPDATE SET
                name = EXCLUDED.name, age = EXCLUDED.age, sobriety = EXCLUDED.sobriety,
                city = EXCLUDED.city, username = EXCLUDED.username, phone = EXCLUDED.phone, 
                program_info = EXCLUDED.program_info;
        """, (user_id,))
        
        # Удаляем из черновиков
        cur.execute("DELETE FROM sponsor_drafts WHERE user_id = %s;", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        # Обновляем сообщение у админа
        await callback.message.edit_text(f"{callback.message.text}\n\n🟢 АНКЕТА ОДОБРЕНА!")
        
        # Уведомляем пользователя
        try:
            await callback.bot.send_message(
                chat_id=user_id, 
                text="🎉 Поздравляем! Твоя карточка спонсора успешно одобрена модератором и добавлена в общую базу группы «Наурыз»!"
            )
        except Exception:
            pass
            
    except Exception as e:
        logging.error(f"Ошибка при одобрении: {e}")
        await callback.answer("Ошибка базы данных!")

# ОБРАБОТКА НАЖАТИЯ КНОПКИ "ОТКЛОНИТЬ"
@router.callback_query(F.data.startswith("mod_reject:"))
async def reject_sponsor(callback: types.CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("DELETE FROM sponsor_drafts WHERE user_id = %s;", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        await callback.message.edit_text(f"{callback.message.text}\n\n🔴 АНКЕТА ОТКЛОНЕНА.")
        
        try:
            await callback.bot.send_message(
                chat_id=user_id, 
                text="❌ Твоя карточка спонсора была отклонена модератором. Возможно, данные заполнены некорректно. Попробуй заполнить заново."
            )
        except Exception:
            pass
            
    except Exception as e:
        logging.error(f"Ошибка при отклонении: {e}")
        await callback.answer("Ошибка базы данных!")