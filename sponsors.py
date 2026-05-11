from aiogram import Router, F
from aiogram.types import Message
from database import get_all

router = Router()


def card(s):
    return (
        "━━━━━━━━━━━━━━\n"
        "🤝 <b>СПОНСОР</b>\n"
        "━━━━━━━━━━━━━━\n\n"

        f"👤 <b>{s[1]}</b>\n\n"
        f"🎂 Возраст: {s[2]}\n"
        f"🧠 {s[3]}\n"
        f"⏳ {s[4]}\n"
        f"🏙 {s[5]}\n"
        f"📚 {s[6]}\n\n"

        f"📱 {s[7]}\n"
        f"☎️ {s[8]}\n\n"

        f"📌 {s[9]}\n"
        "━━━━━━━━━━━━━━"
    )


@router.message(F.text == "🤝 Спонсоры")
async def show(message: Message):

    data = get_all()

    if not data:
        await message.answer("Нет спонсоров")
        return

    for s in data:
        await message.answer(card(s), parse_mode="HTML")