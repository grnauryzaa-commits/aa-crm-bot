from aiogram import Router, F, types, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database as db
import logging

router = Router()

# ⚠️ ВПИШИТЕ СЮДА СВОЙ ЧИСЛОВОЙ ТЕЛЕГРАМ ID (И ДРУГИХ АДМИНОВ ЧЕРЕЗ ЗАПЯТУЮ)
ADMIN_IDS = [123456789] 

async def send_sponsor_request_to_admin(bot: Bot, tg_id: int, data: dict):
    # Создаем инлайн-кнопки под карточкой для админа
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить карточку", callback_data=f"approve_sp_{tg_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_sp_{tg_id}")
        ]
    ])
    
    admin_text = (
        "🔔 **ЗАЯВКА НА РЕГИСТРАЦИЮ / ОБНОВЛЕНИЕ КАРТОЧКИ**\n"
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
    
    # Рассылаем заявку всем указанным админам
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=admin_text, reply_markup=keyboard, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")

@router.callback_query(F.data.startswith("approve_sp_"))
async def approve_sponsor(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🔒 У тебя нет прав администратора группы.", show_alert=True)
        return

    tg_id = int(callback.data.split("_")[2])
    
    # Переносим данные из черновиков в основную активную таблицу
    success = await db.approve_sponsor_draft(tg_id)
    
    if success:
        await callback.message.edit_text(callback.message.text + "\n\n🟢 **КАРТОЧКА ОДОБРЕНА И ОБНОВЛЕНА В БАЗЕ**")
        await callback.answer("Карточка успешно опубликована!", show_alert=True)
        
        # Уведомляем самого спонсора, что модерация прошла успешно
        try:
            await callback.bot.send_message(
                chat_id=tg_id, 
                text="🟢 **Твоя карточка спонсора успешно проверена и обновлена!** Новые данные по трезвости и опыту внесены в общие списки группы Наурыз. Спасибо за твое служение!"
            )
        except Exception:
            pass
    else:
        await callback.answer("Ошибка: Черновик изменений не найден в базе данных.", show_alert=True)

@router.callback_query(F.data.startswith("decline_sp_"))
async def decline_sponsor(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🔒 У тебя нет прав администратора.", show_alert=True)
        return

    tg_id = int(callback.data.split("_")[2])
    
    # Просто удаляем черновик (старая карточка в основной таблице, если была, останется нетронутой)
    await db.delete_sponsor_draft(tg_id)
    
    await callback.message.edit_text(callback.message.text + "\n\n🔴 **ИЗМЕНЕНИЯ ОТКЛОНЕНЫ АДМИНИСТРАТОРОМ**")
    await callback.answer("Заявка отклонена.", show_alert=True)
    
    # Уведомляем пользователя
    try:
        await callback.bot.send_message(
            chat_id=tg_id, 
            text="ℹ️ Предложенные изменения в твоей карточке спонсора были отклонены модератором. В базе осталась твоя прежняя карточка."
        )
    except Exception:
        pass