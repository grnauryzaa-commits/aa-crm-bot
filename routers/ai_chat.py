import logging
from ai_helper import ask_ai_for_beginner
from aiogram import F, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_user_language

router = Router()


@router.message(F.text)
async def handle_beginner_questions(message: types.Message):
    logging.warning(
        f"🚨 [AI_CHAT СРАБОТАЛ!] Тип чата: {message.chat.type} | ID чата:"
        f" {message.chat.id} | Текст: {message.text}"
    )

    # Бот отвечает ТОЛЬКО в личных сообщениях
    if message.chat.type != "private":
        logging.warning(
            "🛑 [БЛОКИРОВКА] Сообщение отброшено, так как это не личный чат."
        )
        return

    menu_buttons = [
        "📖 Ежедневные размышления",
        "📖 Күнделікті ой-толғаулар",
        "🙏 11 Шаг",
        "🙏 11 Қадам",
        "➕ Стать спонсором",
        "➕ Демеуші болу",
        "🤝 Спонсоры",
        "🤝 Демеушілер",
        "📅 Расписание",
        "📅 Кесте",
        "🗓 Расписание",
        "🗓 Кесте",
        "❓ Помощь",
        "❓ Көмек",
        "? Помощь",
        "? Көмек",
        "🌐 Язык: Русский",
        "🌐 Тіл: Қазақша",
        "🏠 Главное меню",
        "🏠 Басты мәзір",
        "📖 Литература АА",
        "📖 АА Әдебиеті",
    ]

    if message.text in menu_buttons:
        return

    # Страховка: если текст начинается с эмодзи кнопок меню — не обрабатываем
    if message.text and message.text.startswith(
        ("📖", "🙏", "➕", "🤝", "📅", "🗓", "❓", "?", "🌐", "🏠")
    ):
        return

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
                    text=servant_button_text, callback_data="call_servant"
                )
            ]
        ]
    )

    await message.answer(
        ai_response, parse_mode="Markdown", reply_markup=servant_keyboard
    )