from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import add_sponsor
from storage import pending_forms

router = Router()


# ✅ ПРИНЯТЬ
@router.callback_query(F.data.startswith("ok_"))
async def approve(call: CallbackQuery):

    uid = int(call.data.split("_")[1])

    data = pending_forms.pop(uid, None)

    if data:
        add_sponsor((
            data["name"],
            data["age"],
            data["identity"],
            data["sobriety"],
            data["city"],
            data["formats"],
            data["telegram"],
            data["phone"],
            data["about"]
        ))

        await call.message.answer("✅ Принято в CRM")

    else:
        await call.message.answer("⚠️ Уже обработано")

    await call.answer()


# ❌ ОТКЛОНИТЬ
@router.callback_query(F.data.startswith("no_"))
async def reject(call: CallbackQuery):

    uid = int(call.data.split("_")[1])

    pending_forms.pop(uid, None)

    await call.message.answer("❌ Отклонено")

    await call.answer()