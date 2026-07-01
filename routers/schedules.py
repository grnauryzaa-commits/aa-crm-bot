from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Главное меню
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Онлайн группы", callback_data="s_online")],
        [InlineKeyboardButton(text="📍 Алматы: Жубанова 3а", callback_data="s_zhub")],
        [InlineKeyboardButton(text="📍 Алматы: Зенкова 24", callback_data="s_zenk")],
        [InlineKeyboardButton(text="📍 Алматы: Тимирязева 42", callback_data="s_tim")],
        [InlineKeyboardButton(text="📍 Другие локации", callback_data="s_other")]
    ])

@router.message(F.text == "📅 Расписание")
async def show_schedule_menu(message: types.Message):
    await message.answer("📅 <b>Расписание собраний АА</b>\nВыберите локацию:", reply_markup=get_main_menu(), parse_mode="HTML")

@router.callback_query(F.data.startswith("s_"))
async def callback_schedule(callback: types.CallbackQuery):
    data = callback.data
    kb = [[InlineKeyboardButton(text="⬅️ Назад", callback_data="s_back")]]
    
    if data == "s_back":
        await callback.message.edit_text("📅 <b>Расписание собраний АА</b>\nВыберите локацию:", reply_markup=get_main_menu(), parse_mode="HTML")
    
    elif data == "s_online":
        text = ("🌐 <b>ОНЛАЙН</b>\n\n• <b>Пробуждение</b>: Вт, Чт, Сб 21:00\n<a href='https://us06web.zoom.us/j/82036099070'>Zoom</a> | Пароль: +77754565358\n\n"
                "• <b>Бірлік (каз)</b>: Чт 21:00\n<a href='https://us06web.zoom.us/j/7473499478'>Zoom</a> | Пароль: +77074337408\n\n"
                "• <b>Шаг за шагом</b>: Вт 19:00\n<a href='https://t.me/+JqgMpZCz_fY1OTVi'>Telegram</a>")
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML", disable_web_page_preview=True)

    elif data == "s_zhub":
        text = ("🏢 <b>Жубанова 3а (каб 301)</b>\n\n• <b>Виктория</b>: Вт, Чт 19:30, Сб 19:00\n• <b>Шапагат (каз)</b>: Пн, Ср 19:00, Сб 17:00\n• <b>Чайхана (Новички)</b>: Вс 11:00\n• <b>Женский клуб</b>: Вс 13:00")
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

    elif data == "s_zenk":
        text = ("🏢 <b>Зенкова 24 (Дом Офицеров)</b>\n\n• <b>8 марта</b>: Ежедневно 19:00, Вт/Чт 12:00\n• <b>АлмА (Женская)</b>: Сб 12:00\n• <b>ААА (Мужская)</b>: Сб 17:00")
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

    elif data == "s_tim":
        text = ("🏢 <b>Тимирязева 42 (Азия-Мост)</b>\n\n• <b>Друзья Билла</b>: Вт, Чт 12:00\n• <b>Наурыз</b>: Вт, Чт, Пт, Сб 19:00, Вс 15:00")
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

    elif data == "s_other":
        text = ("📍 <b>Другие локации</b>\n\n• <b>Аксай</b> (Райымбека 493): Вс 13:00\n"
                "• <b>НОВЫЕ ОЧКИ</b> (Жибек Жолы 64/47): Пн, Ср, Пт 19:00\n"
                "• <b>Боралдай</b> (Курчатова 13а): Сб 17:00\n"
                "• <b>Талхиз (Талгар)</b> (Муратбаева 26): Пн, Чт, Пт 19:00\n"
                "• <b>Турксиб</b>: Уточнять по тел +77478601105")
        
        # Кнопки с ссылками 2GIS для локаций
        extra_kb = [
            [InlineKeyboardButton(text="📍 Талхиз (2GIS)", url="https://2gis.kz/almaty/geo/70000001045475756/77.234246,43.317702")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="s_back")]
        ]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=extra_kb), parse_mode="HTML")

    await callback.answer()