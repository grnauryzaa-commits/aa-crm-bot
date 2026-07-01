from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Главное меню расписания
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Онлайн группы", callback_data="sched_online")],
        [InlineKeyboardButton(text="🏢 Алматы (Центр/Ауэзовский)", callback_data="sched_alm_1")],
        [InlineKeyboardButton(text="🏢 Алматы (Зенкова/Область)", callback_data="sched_alm_2")]
    ])

# Обработчик кнопки из главного меню
@router.message(F.text == "📅 Расписание")
async def show_schedule_menu(message: types.Message):
    await message.answer("📅 <b>Расписание собраний АА</b>\nВыберите категорию:", 
                         reply_markup=get_main_menu(), parse_mode="HTML")

# Обработчик нажатий на Inline-кнопки
@router.callback_query(F.data.startswith("sched_"))
async def process_schedule(callback: types.CallbackQuery):
    data = callback.data
    
    # Логика возврата в главное меню
    if data == "sched_back":
        await callback.message.edit_text("📅 <b>Расписание собраний АА</b>\nВыберите категорию:", 
                                         reply_markup=get_main_menu(), parse_mode="HTML")
        await callback.answer()
        return

    # Тексты для категорий
    if data == "sched_online":
        text = ("🌐 <b>ОНЛАЙН</b>\n\n"
                "• <b>Пробуждение</b> (Вт, Чт, Сб 21:00)\n"
                "<a href='https://us06web.zoom.us/j/82036099070'>Zoom</a> | Пароль: +77754565358\n\n"
                "• <b>Бірлік (каз)</b> (Чт 21:00)\n"
                "<a href='https://us06web.zoom.us/j/7473499478'>Zoom</a> | Пароль: +77074337408\n\n"
                "• <b>Шаг за шагом</b> (Вт 19:00)\n"
                "<a href='https://t.me/+JqgMpZCz_fY1OTVi'>Telegram чат</a>")
    
    elif data == "sched_alm_1":
        text = ("🏢 <b>Группы (Жубанова / Тимирязева)</b>\n\n"
                "• <b>Виктория</b> (Вт, Чт 19:30, Сб 19:00)\n"
                "Адрес: Жубанова 3а, каб 301\n\n"
                "• <b>Наурыз</b> (Вт, Чт, Пт, Сб 19:00, Вс 15:00)\n"
                "Адрес: Тимирязева 42, корп 23, каб 102")
    
    elif data == "sched_alm_2":
        text = ("🏢 <b>Группы (Зенкова / Область)</b>\n\n"
                "• <b>8 марта</b> (Ежедневно 19:00, Вт/Чт 12:00)\n"
                "Адрес: Зенкова 24 (Дом Офицеров)\n\n"
                "• <b>Талхиз (Талгар)</b> (Пн, Чт, Пт 19:00)\n"
                "Адрес: ул. Муратбаева 26")
    
    # Кнопка возврата в меню внутри каждого списка
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К списку категорий", callback_data="sched_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_kb, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()