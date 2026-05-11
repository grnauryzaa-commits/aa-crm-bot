from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🤝 Спонсоры")],
        [KeyboardButton(text="📖 12 шагов")],
        [KeyboardButton(text="🕊 12 традиций")],
        [KeyboardButton(text="🆘 Мне тяжело")],
        [KeyboardButton(text="➕ Стать спонсором")],
        [KeyboardButton(text="⚙️ Админ панель")]
    ],
    resize_keyboard=True
)