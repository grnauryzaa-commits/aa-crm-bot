import logging

from ai_helper import ask_ai_for_beginner
from aiogram import F, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_user_language, log_user_action

router = Router()


@router.message(F.text)
async def handle_beginner_questions(message: types.Message):
    if message.chat.type != "private":
        return

    menu_buttons = [
        "📖 Ежедневные размышления", "📖 Күнделікті ой-толғаулар",
        "🙏 11 Шаг", "🙏 11 Қадам",
        "➕ Стать спонсором", "➕ Демеуші болу",
        "🤝 Спонсоры", "🤝 Демеушілер",
        "📅 Расписание", "📅 Кесте",
        "🗓 Расписание", "🗓 Кесте",
        "❓ Помощь", "❓ Көмек",
        "? Помощь", "? Көмек",
        "🌐 Язык: Русский", "🌐 Тіл: Қазақша",
        "🏠 Главное меню", "🏠 Басты мәзір",
        "📖 Литература АА", "📖 АА Әдебиеті",
    ]

    if message.text in menu_buttons:
        return

    if message.text and message.text.startswith(
        ("📖", "🙏", "➕", "🤝", "📅", "🗓", "❓", "?", "🌐", "🏠")
    ):
        return

    # Логируем обращение к ИИ
    await log_user_action(
        user_id=message.from_user.id,
        action_type="ai_chat",
        action_name="запрос к ИИ",
    )

    await message.bot.send_chat_action(
        chat_id=message.chat.id, action="typing"
    )

    ai_response = await ask_ai_for_beginner(
        message.from_user.id, message.text
    )

    lang = await get_user_language(message.from_user.id)
    if not lang:
        lang = "ru"

    servant_button_text = (
        "👤 Тірі қызметкерді шақыру"
        if lang == "kk"
        else "👤 Позвать живого служащего"
    )

    servant_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=servant_button_text,
                    callback_data="call_servant",
                )
            ]
        ]
    )

    await message.answer(
        ai_response, parse_mode="", reply_markup=servant_keyboard
    )