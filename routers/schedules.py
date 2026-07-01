from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

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
    
    if data == "sched_back":
        await callback.message.edit_text("📅 <b>Расписание собраний АА</b>\nВыберите категорию:", 
                                         reply_markup=get_main_menu(), parse_mode="HTML")
        await callback.answer()
        return

    # Тексты групп
    if data == "sched_online":
        text = ("🌐 <b>ОНЛАЙН</b>\n\n• <b>Пробуждение</b> (Вт, Чт, Сб 21:00)\n• <b>Бірлік (каз)</b> (Чт 21:00)\n• <b>Шаг за шагом</b> (Вт 19:00)")
    
    elif data == "sched_alm_1":
        text = ("🏢 <b>Центр / Ауэзовский</b>\n\n• <b>Виктория</b> (Жубанова 3а: Вт, Чт 19:30, Сб 19:00)\n• <b>Шапагат (каз)</b> (Жубанова 3а: Пн, Ср 19:00, Сб 17:00)\n• <b>Чайхана (Новички)</b> (Жубанова 3а: Вс 11:00)\n• <b>Аксай</b> (Райымбека 493: Вс 13:00)\n• <b>НОВЫЕ ОЧКИ</b> (Жибек Жолы 64/47: Пн, Ср, Пт 19:00, Сб 14:00)")
    
    elif data == "sched_alm_2":
        text = ("🏢 <b>Зенкова / Тимирязева</b>\n\n• <b>8 марта</b> (Зенкова 24: Ежедневно 19:00, Вт/Чт 12:00)\n• <b>Женский клуб</b> (Зенкова 24: Ср 21:00, Вс 13:00)\n• <b>Мужская ААА</b> (Зенкова 24: Сб 17:00)\n• <b>Наурыз</b> (Тимирязева 42: Вт, Чт, Пт, Сб 19:00, Вс 15:00)\n• <b>Друзья Билла</b> (Тимирязева 42: Вт, Чт 12:00)")
    
    elif data == "sched_alm_3":
        text = ("🏢 <b>Область / Другое</b>\n\n• <b>Талхиз (Талгар)</b> (Муратбаева 26: Пн, Чт, Пт 19:00)\n• <b>Боралдай</b> (Курчатова 13а: Сб 17:00)\n• <b>Турксиб</b> (уточнять по тел: +77478601105)")

    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К списку категорий", callback_data="sched_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_kb, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()