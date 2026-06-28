import psycopg2
import logging
import asyncio
from aiogram import Router, F, Bot, types
from aiogram.types import CallbackQuery
from config import DATABASE_URL as DB_URL, ADMINS

router = Router()

# Синхронные функции работы с базой данных
def _approve_sponsor_in_db(user_id):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sponsors (user_id, name, age, sobriety, city, program_info, username, phone)
        SELECT user_id, name, age, sobriety, city, program_info, username, phone 
        FROM sponsor_drafts WHERE user_id = %s
        ON CONFLICT (user_id) DO UPDATE SET 
            name = EXCLUDED.name, age = EXCLUDED.age, sobriety = EXCLUDED.sobriety,
            city = EXCLUDED.city, program_info = EXCLUDED.program_info, 
            username = EXCLUDED.username, phone = EXCLUDED.phone;
    """, (user_id,))
    cur.execute("DELETE FROM sponsor_drafts WHERE user_id = %s;", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def _reject_sponsor_in_db(user_id):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM sponsor_drafts WHERE user_id = %s;", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

# Хэндлеры для кнопок админа
@router.callback_query(F.data.startswith("adm_appr_"))
async def admin_approve(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[2])
    try:
        await asyncio.to_thread(_approve_sponsor_in_db, user_id)
        await callback.message.edit_text(f"{callback.message.text}\n\n🟢 **АНКЕТА ОДОБРЕНА АДМИНИСТРАТОРОМ**")
        try:
            await bot.send_message(user_id, "🎉 Поздравляем! Ваша анкета спонсора успешно прошла модерацию и добавлена в общий список группы «Наурыз».")
        except Exception:
            pass
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)
    await callback.answer()

@router.callback_query(F.data.startswith("adm_rejl_"))
async def admin_reject(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[2])
    try:
        await asyncio.to_thread(_reject_sponsor_in_db, user_id)
        await callback.message.edit_text(f"{callback.message.text}\n\n❌ **АНКЕТА ОТКЛОНЕНА**")
        try:
            await bot.send_message(user_id, "🕊 Ваша анкета спонсора была отклонена модератором. Вы можете заполнить её заново, проверив корректность данных.")
        except Exception:
            pass
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)
    await callback.answer()

# Функция, отправляющая анкету тебе в личку
async def send_to_moderation(bot: Bot, user_id: int, data: dict):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Одобрить", callback_data=f"adm_appr_{user_id}")
    kb.button(text="❌ Отклонить", callback_data=f"adm_rejl_{user_id}")
    kb.adjust(2)
    
    text = (
        "🔔 **НОВАЯ ЗАЯВКА НА СПОНСОРСТВО**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Имя:** {data.get('name')}\n"
        f"📅 **Возраст:** {data.get('age')}\n"
        f"🕊 **Трезвость:** {data.get('sobriety')}\n"
        f"📍 **Город:** {data.get('city')}\n\n"
        f"📖 **Опыт/Программа:** {data.get('program_info')}\n"
        f"✈️ **Telegram:** {data.get('username')}\n"
        f"📞 **Телефон:** {data.get('phone')}\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Не удалось отправить заявку админу {admin_id}: {e}")