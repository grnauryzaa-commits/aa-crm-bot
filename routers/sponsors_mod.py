import logging, psycopg2
from aiogram import Router, F, Bot, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import DATABASE_URL as DB_URL

ADMIN_ID = 7374545230 
router = Router()

async def send_to_moderation(bot: Bot, user_id: int, data: dict):
    text = (
        f"🔔 Новая анкета!\n"
        f"👤 Имя: {data.get('name')} ({data.get('gender')})\n"
        f"📅 {data.get('age')} лет\n"
        f"📍 {data.get('city')}\n"
        f"📖 {data.get('program_info')}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"mod_approve:{user_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mod_reject:{user_id}")
    ]])
    await bot.send_message(chat_id=ADMIN_ID, text=text, reply_markup=kb)

@router.callback_query(F.data.startswith("mod_approve:"))
async def approve_sponsor(callback: types.CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sponsors 
        SELECT user_id, name, gender, age, sobriety, city, username, phone, program_info 
        FROM sponsor_drafts WHERE user_id = %s 
        ON CONFLICT (user_id) DO UPDATE SET 
            name = EXCLUDED.name, 
            gender = EXCLUDED.gender, 
            age = EXCLUDED.age, 
            sobriety = EXCLUDED.sobriety, 
            city = EXCLUDED.city, 
            username = EXCLUDED.username, 
            phone = EXCLUDED.phone, 
            program_info = EXCLUDED.program_info;
    """, (user_id,))
    cur.execute("DELETE FROM sponsor_drafts WHERE user_id = %s;", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    await callback.message.edit_text(f"{callback.message.text}\n\n✅ Одобрено!")
    await callback.bot.send_message(chat_id=user_id, text="🎉 Твоя анкета одобрена!")

@router.callback_query(F.data.startswith("mod_reject:"))
async def reject_sponsor(callback: types.CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM sponsor_drafts WHERE user_id = %s;", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    await callback.message.edit_text(f"{callback.message.text}\n\n❌ Отклонено.")
    await callback.bot.send_message(chat_id=user_id, text="❌ Твоя анкета была отклонена.")