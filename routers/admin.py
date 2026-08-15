from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
import psycopg2
from config import DATABASE_URL

router = Router()

@router.callback_query(F.data.startswith("approve_sp_"))
async def approve_sponsor(callback: CallbackQuery, bot: Bot):
    target_user_id = int(callback.data.split("_")[2])
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Берем данные из черновика
        cur.execute("SELECT name, gender, age, sobriety, city, username, phone, program_info FROM sponsor_drafts WHERE user_id = %s;", (target_user_id,))
        draft = cur.fetchone()
        
        if draft:
            # Переносим в таблицу sponsors
            cur.execute("""
                INSERT INTO sponsors (user_id, name, gender, age, sobriety, city, username, phone, program_info)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    name = EXCLUDED.name, gender = EXCLUDED.gender, age = EXCLUDED.age,
                    sobriety = EXCLUDED.sobriety, city = EXCLUDED.city, username = EXCLUDED.username,
                    phone = EXCLUDED.phone, program_info = EXCLUDED.program_info;
            """, (target_user_id, *draft))
            
            # Удаляем черновик
            cur.execute("DELETE FROM sponsor_drafts WHERE user_id = %s;", (target_user_id,))
            conn.commit()
            
        cur.close()
        conn.close()

        await callback.message.edit_text(f"{callback.message.text}\n\n✅ ОДОБРЕНО", reply_markup=None)
        await callback.answer("Анкета одобрена!")
        
        try:
            await bot.send_message(target_user_id, "🎉 Ваша анкета спонсора одобрена!")
        except: pass
            
    except Exception as e:
        print(f"Ошибка в approve: {e}")
        await callback.answer("Ошибка БД")

@router.callback_query(F.data.startswith("decline_sp_"))
async def decline_sponsor(callback: CallbackQuery, bot: Bot):
    target_user_id = int(callback.data.split("_")[2])
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("DELETE FROM sponsor_drafts WHERE user_id = %s;", (target_user_id,))
        conn.commit()
        cur.close()
        conn.close()

        await callback.message.edit_text(f"{callback.message.text}\n\n❌ ОТКЛОНЕНО", reply_markup=None)
        await callback.answer("Анкета отклонена.")
    except Exception as e:
        print(f"Ошибка в decline: {e}")