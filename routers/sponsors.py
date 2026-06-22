from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import database as db

router = Router()

@router.message(F.text == "🤝 Спонсоры")
async def show_sponsors_list(message: Message):
    sponsors = db.get_all()
    if not sponsors:
        return await message.answer("На данный момент список спонсоров пуст. Будь первым!")

    text = "🤝 **Список доступных спонсоров:**\nНажмите на кнопку ниже, чтобы открыть карточку.\n"
    buttons = []
    
    for s in sponsors:
        # s = (id, name, city, sobriety)
        btn_text = f"{s[1]} | {s[2]} | Трезвость: {s[3]}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"view_{s[0]}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=kb)

@router.callback_query(F.data.startswith("view_"))
async def show_sponsor_card(call: CallbackQuery):
    sp_id = int(call.data.split("_")[1])
    s = db.get_sponsor_by_id(sp_id)

    if not s:
        return await call.answer("Спонсор не найден!", show_alert=True)

    # s = (id, name, age, identity, sobriety, city, formats, telegram, phone, about)
    card_text = (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 КАРТОЧКА СПОНСОРА #{s[0]}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 **Имя:** {s[1]} ({s[2]} лет)\n"
        f"🧠 **Идентификация:** {s[3]}\n"
        f"⏳ **Срок трезвости:** {s[4]}\n"
        f"🏙 **Город:** {s[5]}\n"
        f"📚 **Формат работы:** {s[6]}\n"
        f"☎️ **Телефон:** {s[8]}\n\n"
        f"📌 **О себе:**\n{s[9]}"
    )

    # Формируем ссылку на телеграм для кнопки связи
    tg_username = s[7].replace("@", "").strip()
    url = f"https://t.me/{tg_username}"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📱 Написать в Telegram", url=url)],
            [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="back_to_list")]
        ]
    )

    await call.message.edit_text(card_text, reply_markup=kb, parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data == "back_to_list")
async def back_to_list(call: CallbackQuery):
    sponsors = db.get_all()
    if not sponsors:
        return await call.message.edit_text("Список спонсоров пуст.")

    buttons = []
    for s in sponsors:
        btn_text = f"{s[1]} | {s[2]} | Трезвость: {s[3]}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"view_{s[0]}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("🤝 **Список доступных спонсоров:**", reply_markup=kb)
    await call.answer()