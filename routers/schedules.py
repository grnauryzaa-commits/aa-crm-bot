from aiogram import F, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_user_language

router = Router()

TEXTS = {
    "ru": {
        "title": "📅 <b>Расписание собраний АА</b>\nВыберите город:",
        "help_text": "\n\nЕсли у вас есть вопросы, нужна поддержка — мы готовы помочь.\n📞 Горячая линия: +7 (707) 208-05-53",
        "back": "⬅️ Назад",
        "no_schedule": "Для этой группы пока нет расписания."
    },
    "kk": {
        "title": "📅 <b>АА жиналыстарының кестесі</b>\nҚаланы таңдаңыз:",
        "help_text": "\n\nЕгер сұрақтарыңыз болса, көмек керек болса — біз көмектесуге дайынбыз.\n📞 Жедел желі: +7 (707) 433-74-08",
        "back": "⬅️ Артқа",
        "no_schedule": "Бұл топ үшін әзірге кесте жоқ."
    }
}

SCHEDULE_DATA = {
    "Алматы": [
        "• <b>АА «Виктория»</b>\n📍 Адрес: г. Алматы, ул. Жубанова 3а\n⏰ Время: Вт, Чт 19:30-21:00; Сб 19:00-20:30\n📞 Контакты: +7 705-990-79-38",
        "• <b>АА «8 марта»</b>\n📍 Адрес: г. Алматы, ул. Зенкова 24\n⏰ Время: Ежедневно 19:00-20:30\n📞 Контакты: +7 701-121-85-01",
        "• <b>АА «Турксиб»</b>\n📍 Адрес: Уточнять по номеру\n⏰ Время: Вт, Чт 19:00-20:30; Вс 17:00-18:30\n📞 Контакты: +7 747-860-11-05",
        "• <b>АА женская «АлмА»</b>\n📍 Адрес: г. Алматы, ул. Зенкова 24\n⏰ Время: Сб 12:00-13:30\n📞 Контакты: +7 775-500-68-46",
        "• <b>АА «Шапагат» на казахском языке</b>\n📍 Адрес: г. Алматы, ул. Жубанова 3а\n⏰ Время: Пн, Ср 19:00-20:30; Сб 17:00-18:30\n📞 Контакты: +7 747-165-2435",
        "• <b>АА «Друзья Билла»</b>\n📍 Адрес: г. Алматы, ул. Бухар Жырау 66\n⏰ Время: Вт, Чт 12:00-13:00\n📞 Контакты: +7 747-563-75-87",
        "• <b>АА «Чайхана»</b>\n📍 Адрес: г. Алматы, ул. Жубанова 3а\n⏰ Время: Ср, Пт 19:30; Вс 11:00-12:30\n📞 Контакты: +7 708-986-35-50",
        "• <b>АА «Аксай»</b>\n📍 Адрес: г. Алматы, Пр. Райымбека 493\n⏰ Время: Вс 13:00-14:15\n📞 Контакты: +7 776-453-3418",
        "• <b>АА «Наурыз»</b>\n📍 Адрес: г. Алматы, ул. Бухар Жырау 66\n⏰ Время: Вт, Чт, Сб 19:00-20:30; Вс 15:00-16:30\n📞 Контакты: +7 708-317-17-69",
        "• <b>АА «qazan»</b>\n⏰ Время: Пн, Ср, Пт 19:00-20:30\n📞 Контакты: +7 707-909-02-25",
        "• <b>АА «НОВЫЕ ОЧКИ»</b>\n📍 Адрес: г. Алматы, ул. Жибек Жолы 64/47\n⏰ Время: Пн, Ср, Пт 19:00-20:15; Сб 14:00\n📞 Контакты: +7 707-308-47-57",
        "• <b>АА «боралдай»</b>\n📍 Адрес: г. Алматы, ул. Курчатова 13а\n⏰ Время: Сб 17:00\n📞 Контакты: +7 777-281-90-98",
        "• <b>Мужская группа «ААА»</b>\n📍 Адрес: г. Алматы, ул. Зенкова 24\n⏰ Время: Сб 17:00-18:15\n📞 Контакты: +7 771 370 9966",
        "• <b>Талгар «талхиз»</b>\n📍 Адрес: г. Талгар, ул. Муратбаева 26\n⏰ Время: Пн, Чт 18:00; Сб 16:00\n📞 Контакты: +7-747-420-5862",
        "• <b>каскелен «туран»</b>\n📍 Адрес: г. Каскелен, ул. Конаева 8\n⏰ Время: Пн, Ср, Сб 17:00-18:15\n📞 Контакты: +7-777-063-0838"
    ],
    "Астана": [
        "• <b>АА «51 параллель»</b>\n📍 Адрес: г. Астана, ул. Петрова 14/3\n⏰ Время: Ср 19:00-20:15; Сб 15:00-16:15\n📞 Контакты: +7 771-899-36-79",
        "• <b>АА «Свобода»</b>\n📍 Адрес: г. Астана, ул. Петрова 14/3\n⏰ Время: Пн, Чт, Пт 19:00-20:00\n📞 Контакты: +7 771-899-36-79",
        "• <b>АА «Есиль» (каз)</b>\n📍 Адрес: г. Астана, ул. Петрова 14/3\n⏰ Время: Вс 17:00-18:30\n📞 Контакты: +7-775-360-15-28",
        "• <b>АА «Большая перемена»</b>\n📍 Адрес: г. Астана, ул. Дукенулы 26\n⏰ Время: Пн, Пт 19:00-20:00\n📞 Контакты: +7-707-123-46-99",
        "• <b>АА «Сана»</b>\n📍 Адрес: г. Астана, пр. Кабанбай Батыра 58 А\n⏰ Время: Вт, Чт 20:00-21:15\n📞 Контакты: +7 771-899-36-79",
        "• <b>АА «Путь»</b>\n📍 Адрес: г. Астана, ул. Ташенова 26\n⏰ Время: Вт, Ср, Чт 19:00-20:15\n📞 Контакты: +7 771-899-36-79",
        "• <b>АА «Возрождение»</b>\n📍 Адрес: г. Астана, ул. Куйши Дина, д. 27\n⏰ Время: Вт 19:00-20:15\n📞 Контакты: +7 707-565-05-86",
        "• <b>АА «Гармония»</b>\n📍 Адрес: г. Астана, ул. Арасан 2/2\n⏰ Время: Пн, Пт 19:15\n📞 Контакты: +7-775-360-15-28",
        "• <b>АА «Үміт» (каз)</b>\n📍 Адрес: г. Астана, ул. Шакарима 94\n⏰ Время: Ср 19:00-20:15\n📞 Контакты: +7-707-433-7408",
        "• <b>АА «Венера»</b>\n📍 Адрес: г. Астана, ул. Куйши Дина 27/1\n⏰ Время: Сб 15:00\n📞 Контакты: +7-771-899-3679"
    ],
    "Онлайн": [
        "• <b>АА «Пробуждение»</b>\n💻 Zoom: https://us06web.zoom.us/j/82036099070\n⏰ Время: Вт, Чт, Сб 21:00-22:30\n🔑 Пароль: +7 775-456-53-58",
        "• <b>АА «Бірлік» (каз)</b>\n💻 Zoom: https://us06web.zoom.us/j/7473499478\n⏰ Время: Чт 21:00-22:30\n🔑 Пароль: +7 707-433-74-08",
        "• <b>АА «Шаг за шагом»</b>\n💬 Telegram: https://t.me/+JqgMpZCz_fY1OTVi\n⏰ Время: Вт 19:00-20:30",
        "• <b>АА «АРНА»</b>\n💬 WhatsApp: https://chat.whatsapp.com/JtTlAERQHu26RJ6WMSxazm\n⏰ Время: Пн, Пт 21:00\n📞 Телефон: +77476845424"
    ]
}

def get_cities_kb(lang="ru"):
    kb = []
    row = []
    cities = sorted(SCHEDULE_DATA.keys())
    
    for city in cities:
        row.append(InlineKeyboardButton(text=city, callback_data=f"s_{city}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

@router.message(F.chat.type == "private", F.text.in_({"📅 Расписание", "📅 Кесте"}))
async def show_schedule_menu(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    if not lang: lang = "ru"
    
    await message.answer(
        TEXTS[lang]["title"],
        reply_markup=get_cities_kb(lang),
        parse_mode="HTML",
    )

@router.callback_query(F.data.startswith("s_"))
async def callback_schedule(callback: types.CallbackQuery):
    data_str = callback.data
    lang = await get_user_language(callback.from_user.id)
    if not lang: lang = "ru"
    t = TEXTS[lang]

    if data_str == "s_back":
        await callback.message.edit_text(t["title"], reply_markup=get_cities_kb(lang), parse_mode="HTML")
        await callback.answer()
        return

    elif data_str.startswith("s_"):
        city_name = data_str.replace("s_", "")
        groups = SCHEDULE_DATA.get(city_name)
        
        if not groups:
            await callback.answer(t["no_schedule"], show_alert=True)
            return
            
        await callback.bot.send_message(callback.from_user.id, f"🏙 <b>{city_name}</b>", parse_mode="HTML")
        
        for group in groups:
            await callback.bot.send_message(callback.from_user.id, group, parse_mode="HTML")
            
        kb = [[InlineKeyboardButton(text=t["back"], callback_data="s_back")]]
        await callback.bot.send_message(callback.from_user.id, t["help_text"], reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

    await callback.answer()