from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🤝 Спонсоры"), KeyboardButton(text="➕ Стать спонсором")],
        [KeyboardButton(text="📖 Ежедневные размышления")],
        [KeyboardButton(text="🆘 Мне тяжело"), KeyboardButton(text="⚙️ Админ панель")]
    ],
    resize_keyboard=True
)