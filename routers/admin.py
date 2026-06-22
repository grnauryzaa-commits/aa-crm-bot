from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from database import add_sponsor
from storage import pending_forms
from config import ADMIN_IDS

router = Router()

@router.message(F.text == "⚙️ Админ панель")
async def admin_panel(message: Message):
    if message.from_user.id in ADMIN_IDS:
        await message.answer("⚙️ Добро пожаловать в панель управления. Сюда приходят анкеты на модерацию.")
    else:
        await message.answer("🔒 Доступ ограничен.")

@router.callback_query(F.data.startswith("ok_"))
async def approve(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return await call.answer("У вас нет прав!", show_alert=True)

    uid = int(call.data.split("_")[1])
    data = pending_forms.pop(uid, None)

    if data:
        add_sponsor((
            data["name"], data["age"], data["identity"], data["sobriety"],
            data["city"], data["formats"], data["telegram"], data["phone"], data["about"]
        ))
        await call.message.edit_text(call.message.text + "\n\n✅ **АНКЕТА ПРИНЯТА В БД**")
        try:
            await call.bot.send_message(uid, "🎉 Поздравляем! Ваша анкета спонсора была одобрена администратором.")
        except Exception:
            pass
    else:
        await call.message.answer("⚠️ Данная анкета уже была обработана кем-то другим.")
    await call.answer()

@router.callback_query(F.data.startswith("no_"))
async def reject(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return await call.answer("У вас нет прав!", show_alert=True)

    uid = int(call.data.split("_")[1])
    pending_forms.pop(uid, None)

    await call.message.edit_text(call.message.text + "\n\n❌ **АНКЕТА ОТКЛОНЕНА**")
    try:
        await call.bot.send_message(uid, "❌ К сожалению, ваша заявка на спонсорство была отклонена модератором.")
    except Exception:
        pass
    await call.answer()