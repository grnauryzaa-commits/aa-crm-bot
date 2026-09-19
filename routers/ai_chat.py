from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ai_helper import ask_ai_for_beginner
import logging

router = Router()

@router.message(F.text)
async def handle_beginner_questions(message: types.Message):
    # Принудительно логируем каждое сообщение, попавшее в ai_chat
    logging.warning(f"🚨 [AI_CHAT СРАБОТАЛ!] Тип чата: {message.chat.type} | ID чата: {message.chat.id} | Текст: {message.text}")

    # ЖЕСТКИЙ ЗАПРЕТ: Бот отвечает ТОЛЬКО в личных сообщениях
    if message.chat.type != "private":
        logging.warning("🛑 [БЛОКИРОВКА] Сообщение отброшено, так как это не личный чат.")
        return

    menu_buttons = [
        "📖 Ежедневные размышления", 
        "🙏 11 Шаг", 
        "➕ Стать спонсором", 
        "🤝 Спонсоры", 
        "📅 Расписание", 
        "❓ Помощь"
    ]
    if message.text in menu_buttons:
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    ai_response = await ask_ai_for_beginner(message.from_user.id, message.text)

    servant_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Позвать живого служащего", callback_data="call_servant")]
        ]
    )

    await message.answer(
        ai_response, 
        parse_mode="Markdown", 
        reply_markup=servant_keyboard
    )