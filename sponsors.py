from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from database import get_all, get_sponsor_by_id

router = Router()


# =====================================================
# СПИСОК СПОНСОРОВ
# =====================================================

@router.message(F.text == "🤝 Спонсоры")
async def show_sponsors(message: Message):

    sponsors = get_all()

    if not sponsors:
        await message.answer(
            "❌ Спонсоры пока отсутствуют"
        )
        return

    sponsors = sorted(
        sponsors,
        key=lambda x: x[1].lower()
    )

    buttons = []

    for sponsor in sponsors:

        sponsor_id = sponsor[0]
        sponsor_name = sponsor[1]
        city = sponsor[5]

        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {sponsor_name} • {city}",
                callback_data=f"sponsor_{sponsor_id}"
            )
        ])

    kb = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await message.answer(
        "━━━━━━━━━━━━━━\n"
        "🤝 СПОНСОРЫ\n"
        "━━━━━━━━━━━━━━\n\n"
        "Выберите спонсора:",
        reply_markup=kb
    )


# =====================================================
# КАРТОЧКА СПОНСОРА
# =====================================================

@router.callback_query(
    F.data.startswith("sponsor_")
)
async def sponsor_card(
    callback: CallbackQuery
):

    sponsor_id = int(
        callback.data.split("_")[1]
    )

    sponsor = get_sponsor_by_id(
        sponsor_id
    )

    if not sponsor:

        await callback.answer(
            "Спонсор не найден",
            show_alert=True
        )

        return

    (
        sid,
        name,
        age,
        identity,
        sobriety,
        city,
        formats,
        telegram,
        phone,
        about
    ) = sponsor

    text = (
        "━━━━━━━━━━━━━━\n"
        "🤝 СПОНСОР\n"
        "━━━━━━━━━━━━━━\n\n"

        f"👤 {name}\n\n"

        f"🎂 Возраст: {age}\n"
        f"🧠 {identity}\n"
        f"⏳ {sobriety}\n"
        f"🏙 {city}\n"
        f"📚 {formats}\n\n"

        f"📱 {telegram}\n"
        f"☎️ {phone}\n\n"

        f"📌 {about}\n"

        "━━━━━━━━━━━━━━"
    )

    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅ Назад к списку",
                    callback_data="back_to_sponsors"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_kb
    )

    await callback.answer()


# =====================================================
# НАЗАД К СПИСКУ
# =====================================================

@router.callback_query(
    F.data == "back_to_sponsors"
)
async def back_to_sponsors(
    callback: CallbackQuery
):

    sponsors = get_all()

    sponsors = sorted(
        sponsors,
        key=lambda x: x[1].lower()
    )

    buttons = []

    for sponsor in sponsors:

        sponsor_id = sponsor[0]
        sponsor_name = sponsor[1]
        city = sponsor[5]

        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {sponsor_name} • {city}",
                callback_data=f"sponsor_{sponsor_id}"
            )
        ])

    kb = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await callback.message.edit_text(
        "━━━━━━━━━━━━━━\n"
        "🤝 СПОНСОРЫ\n"
        "━━━━━━━━━━━━━━\n\n"
        "Выберите спонсора:",
        reply_markup=kb
    )

    await callback.answer()