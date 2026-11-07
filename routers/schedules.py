from aiogram import F, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_user_language
import psycopg2
from config import DATABASE_URL

router = Router()

TEXTS = {
    "ru": {
        "title": "📅 <b>Расписание собраний АА</b>\nВыберите город:",
        "online": "🌐 <b>ОНЛАЙН ГРУППЫ</b>\n\n• <b>Пробуждение</b>: Вт, Чт, Сб 21:00\n<a href='https://us06web.zoom.us/j/82036099070'>Zoom</a> | Пароль: +77754565358\n\n• <b>Бірлік (каз)</b>: Чт 21:00\n<a href='https://us06web.zoom.us/j/7473499478'>Zoom</a> | Пароль: +77074337408\n\n• <b>Шаг за шагом</b>: Вт 19:00\n<a href='https://t.me/+JqgMpZCz_fY1OTVi'>Telegram</a>",
        "help_text": "\n\nЕсли у вас есть вопросы, нужна поддержка — мы готовы помочь.\n📞 Горячая линия: +7 (707) 208-05-53",
        "back": "⬅️ Назад",
        "2gis": "📍 Открыть в 2GIS",
        "btn_online": "🌐 Онлайн группы",
        "btn_almaty": "🏙 Алматы",
        "btn_astana": "🏙 Астана",
        "almaty": "🏙 <b>Группы в Алматы</b>\nВыберите группу:",
        "astana": "🏙 <b>Группы в Астане</b>\nВыберите группу:",
    },
    "kk": {
        "title": "📅 <b>АА жиналыстарының кестесі</b>\nҚаланы таңдаңыз:",
        "online": "🌐 <b>ОНЛАЙН ТОПТАР</b>\n\n• <b>Пробуждение</b>: Сей, Бей, Сен 21:00\n<a href='https://us06web.zoom.us/j/82036099070'>Zoom</a>\n\n• <b>Бірлік</b>: Бей 21:00\n<a href='https://us06web.zoom.us/j/7473499478'>Zoom</a>",
        "help_text": "\n\nЕгер сұрақтарыңыз болса, көмек керек болса — біз көмектесуге дайынбыз.\n📞 Жедел желі: +7 (707) 433-74-08",
        "back": "⬅️ Артқа",
        "2gis": "📍 2GIS-тен ашу",
        "btn_online": "🌐 Онлайн топтар",
        "btn_almaty": "🏙 Алматы",
        "btn_astana": "🏙 Астана",
        "almaty": "🏙 <b>Алматы қаласындағы топтар</b>\nТопты таңдаңыз:",
        "astana": "🏙 <b>Астана қаласындағы топтар</b>\nТопты таңдаңыз:",
    }
}

def get_unique_cities():
    """Берет список городов из базы, кроме Алматы и Астаны."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT city, MIN(sort_order) FROM aa_schedule WHERE city NOT IN ('Алматы', 'Астана') GROUP BY city ORDER BY MIN(sort_order);")
    cities = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return cities

def get_cities_kb(lang="ru"):
    t = TEXTS[lang]
    cities = get_unique_cities()
    
    keyboard = [
        [InlineKeyboardButton(text=t["btn_online"], callback_data="s_online")],
        [InlineKeyboardButton(text=t["btn_almaty"], callback_data="s_city_Алматы"),
         InlineKeyboardButton(text=t["btn_astana"], callback_data="s_city_Астана")]
    ]
    
    # Автоматически распределяем остальные города по 2 в ряд
    row = []
    for city in cities:
        row.append(InlineKeyboardButton(text=city, callback_data=f"s_city_{city}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(F.chat.type == "private", F.text.in_({"📅 Расписание", "📅 Кесте"}))
async def show_schedule_menu(message: types.Message):
    lang = await get_user_language(message.from_user.id) or "ru"
    await message.answer(TEXTS[lang]["title"], reply_markup=get_cities_kb(lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("s_"))
async def callback_schedule(callback: types.CallbackQuery):
    data = callback.data
    lang = await get_user_language(callback.from_user.id) or "ru"
    t = TEXTS[lang]

    if data == "s_back":
        await callback.message.edit_text(t["title"], reply_markup=get_cities_kb(lang), parse_mode="HTML")
        
    elif data == "s_online":
        text = t["online"] + t["help_text"]
        kb = [[InlineKeyboardButton(text=t["back"], callback_data="s_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML", disable_web_page_preview=True)

    elif data.startswith("s_city_"):
        city_name = data.replace("s_city_", "")
        
        # Если это Алматы или Астана, показываем список групп кнопками
        if city_name in ["Алматы", "Астана"]:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("SELECT id, group_name FROM aa_schedule WHERE city = %s ORDER BY id;", (city_name,))
            groups = cur.fetchall()
            cur.close()
            conn.close()
            
            if not groups:
                await callback.answer("В этом городе пока нет расписания.", show_alert=True)
                return
                
            text = t["almaty"] if city_name == "Алматы" else t["astana"]
            keyboard = []
            for group_id, group_name in groups:
                keyboard.append([InlineKeyboardButton(text=group_name, callback_data=f"s_group_{group_id}")])
            
            keyboard.append([InlineKeyboardButton(text=t["back"], callback_data="s_back")])
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")

        else:
            # Для остальных городов сразу выводим текст (там обычно 1-2 группы)
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("SELECT group_name, address, time_info, contacts FROM aa_schedule WHERE city = %s ORDER BY id;", (city_name,))
            groups = cur.fetchall()
            cur.close()
            conn.close()
            
            text = f"🏙 <b>{city_name}</b>\n\n"
            for group in groups:
                g_name, addr, time_inf, cont = group
                text += f"🔹 <b>{g_name}</b>\n"
                if addr: text += f"📍 {addr}\n"
                if time_inf: text += f"🕒 {time_inf}\n"
                if cont: text += f"📞 {cont}\n\n"
            text += t["help_text"]
            
            kb = [[InlineKeyboardButton(text=t["back"], callback_data="s_back")]]
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

    # Показ конкретной группы (для Алматы и Астаны)
    elif data.startswith("s_group_"):
        group_id = data.replace("s_group_", "")
        
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT city, group_name, address, time_info, contacts FROM aa_schedule WHERE id = %s;", (group_id,))
        group = cur.fetchone()
        cur.close()
        conn.close()
        
        if group:
            city, g_name, addr, time_inf, cont = group
            text = f"🔹 <b>{g_name}</b>\n"
            if addr: text += f"📍 {addr}\n"
            if time_inf: text += f"🕒 {time_inf}\n"
            if cont: text += f"📞 {cont}\n"
            text += t["help_text"]
            
            kb = [[InlineKeyboardButton(text=t["back"], callback_data=f"s_city_{city}")]]
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")
        else:
            await callback.answer("Группа не найдена.", show_alert=True)

    await callback.answer()