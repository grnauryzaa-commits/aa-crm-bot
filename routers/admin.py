from aiogram import Router, F, types, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database as db
import logging

router = Router()

ADMIN_IDS = [123456789] # Твой реальный Telegram ID цифрами

async def send_sponsor_request_to_admin(bot: Bot, tg_id: int, data: dict):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить изменения", callback_data=f"approve_sp_{tg_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_sp_{tg_id}")
        ]
    ])
    
    admin_text = (
        "🔔 **ЗАЯВКА НА ОБНОВЛЕНИЕ/РЕГИСТРАЦИЮ КАРТОЧКИ**\n"
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
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=admin_text, reply_markup=keyboard, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Не удалось отправить админу {admin_id}: {e}")

@router.callback_query(F.data.startswith("approve_sp_"))
async def approve_sponsor(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🔒 Доступ закрыт.", show_alert=True)
        return

    tg_id = int(callback.data.split("_")[2])
    success = await db.approve_sponsor_draft(tg_id)
    
    if success:
        await callback.message.edit_text(callback.message.text + "\n\n🟢 **ОДОБРЕНО И ОБНОВЛЕНО В БАЗЕ**")
        await callback.answer("Карточка успешно обновлена!", show_alert=True)
        
        try:
            await callback.bot.send_message(
                chat_id=tg_id, 
                text="🟢 **Твоя карточка спонсора успешно обновлена и опубликована!** Новые данные по трезвости и опыту внесены в базу данных группы Наурыз."
            )
        except Exception:
            pass
    else:
        await callback.answer("Ошибка: Черновик не найден.", show_alert=True)

@router.callback_query(F.data.startswith("decline_sp_"))
async def decline_sponsor(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🔒 Доступ закрыт.", show_alert=True)
        return

    tg_id = int(callback.data.split("_")[2])
    await db.delete_sponsor_draft(tg_id)
    
    await callback.message.edit_text(callback.message.text + "\n\n🔴 **ИЗМЕНЕНИЯ ОТКЛОНЕНЫ**")
    await callback.answer("Заявка отклонена.", show_alert=True)
    
    try:
        await callback.bot.send_message(
            chat_id=tg_id, 
            text="ℹ️ Изменения в твоей карточке спонсора были отклонены модератором. В базе осталась старая версия."
        )
    except Exception:
        pass