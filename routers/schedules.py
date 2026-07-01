from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Функция главного меню
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Онлайн группы", callback_data="sched_online")],
        [InlineKeyboardButton(text="🏢 Алматы: Центр / Ауэзовский", callback_data="sched_alm_1")],
        [InlineKeyboardButton(text="🏢 Алматы: Зенкова / Тимирязева", callback_data="sched_alm_2")],
        [InlineKeyboardButton(text="🏢 Алматы: Область / Другое", callback_data="sched_alm_3")]
    ])

@router.message(F.text == "📅 Расписание")
async def show_schedule_menu(message: types.Message):
    await message.answer("📅 <b>Расписание собраний АА</b>\nВыберите категорию:", 
                         reply_markup=get_main_menu(), parse_mode="HTML")

@router.callback_query(F.data.startswith("sched_"))
async def process_schedule(callback: types.CallbackQuery):
    data = callback.data
    
    # Кнопка назад
    if data == "sched_back":
        await callback.message.edit_text("📅 <b>Расписание собраний АА</b>\nВыберите категорию:", 
                                         reply_markup=get_main_menu(), parse_mode="HTML")
        await callback.answer()
        return

    # --- ТЕКСТЫ И КНОПКИ ГЕОЛОКАЦИИ ---
    text = ""
    buttons = []

    if data == "sched_online":
        text = "🌐 <b>ОНЛАЙН</b>\n\n• <b>Пробуждение</b> (Вт, Чт, Сб 21:00)\n• <b>Бірлік (каз)</b> (Чт 21:00)\n• <b>Шаг за шагом</b> (Вт 19:00)"
    
    elif data == "sched_alm_1":
        text = "🏢 <b>Центр / Ауэзовский</b>\n\n• <b>Виктория / Шапагат / Чайхана</b> (Жубанова 3а)\n• <b>Аксай</b> (Райымбека 493)\n• <b>НОВЫЕ ОЧКИ</b> (Жибек Жолы 64/47)"
        buttons.append([InlineKeyboardButton(text="📍 Виктория (2GIS)", url="https://2gis.kz/almaty/geo/9430047374991567/76.9066,43.2389")])
    
    elif data == "sched_alm_2":
        text = "🏢 <b>Зенкова / Тимирязева</b>\n\n• <b>8 марта / Женская / Мужская</b> (Зенкова 24)\n• <b>Наурыз / Друзья Билла</b> (Тимирязева 42, Азия-Мост)"
        buttons.append([InlineKeyboardButton(text="📍 8 марта (2GIS)", url="https://2gis.kz/almaty/search/%D0%97%D0%B5%D0%BD%D0%BA%D0%BE%D0%B2%D0%B0%2024")])
        buttons.append([InlineKeyboardButton(text="📍 Азия-Мост (2GIS)", url="https://2gis.kz/almaty/firm/70000001035652591")])
    
    elif data == "sched_alm_3":
        text = "🏢 <b>Область / Другое</b>\n\n• <b>Талхиз (Талгар)</b> (Муратбаева 26)\n• <b>Боралдай</b> (Курчатова 13а)"
        buttons.append([InlineKeyboardButton(text="📍 Талхиз (2GIS)", url="https://2gis.kz/almaty/geo/70000001045475756/77.234246,43.317702")])

    # Добавляем кнопку "Назад" в конец списка
    buttons.append([InlineKeyboardButton(text="⬅️ К списку категорий", callback_data="sched_back")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()