from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ai_helper import ask_ai_for_beginner

router = Router()

# ID канала/чата Наурыз, куда бот отправляет рассылку и должен молчать на обычные сообщения
NAURYZ_CHAT_ID = -1002140833802

@router.message(F.text)
async def handle_beginner_questions(message: types.Message):
    # Жесткий фильтр: если сообщение написано в чате Наурыза, бот молчит и не отвечает
    if message.chat.id == NAURYZ_CHAT_ID:
        return

    # Дополнительная страховка на случай попадания служебных текстов
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

    # Отправляем статус "печатает..."
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Запрос к искусственному интеллекту
    ai_response = await ask_ai_for_beginner(message.from_user.id, message.text)

    # Кнопка связи со служащим
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