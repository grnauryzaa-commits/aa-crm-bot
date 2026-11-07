from aiogram import F, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_user_language
import requests
from bs4 import BeautifulSoup
import logging

router = Router()

TEXTS = {
    "ru": {
        "title": "📅 <b>Расписание собраний АА</b>\nВыберите город:",
        "help_text": "\n\nЕсли у вас есть вопросы, нужна поддержка — мы готовы помочь.\n📞 Горячая линия: +7 (707) 208-05-53",
        "back": "⬅️ Назад",
        "no_schedule": "Для этой группы пока нет расписания.",
        "2gis": "📍 Открыть в 2GIS"
    },
    "kk": {
        "title": "📅 <b>АА жиналыстарының кестесі</b>\nҚаланы таңдаңыз:",
        "help_text": "\n\nЕгер сұрақтарыңыз болса, көмек керек болса — біз көмектесуге дайынбыз.\n📞 Жедел желі: +7 (707) 433-74-08",
        "back": "⬅️ Артқа",
        "no_schedule": "Бұл топ үшін әзірге кесте жоқ.",
        "2gis": "📍 2GIS-тен ашу"
    }
}

# Жестко зашиваем Алматы и Астану, чтобы они не висели
HARDCODED_CITIES = {
    "Алматы": {
        "alm_zhub": '🏢 <b>Жубанова 3а</b>\n\n• <b>Виктория</b>: Вт, Чт 19:30, Сб 19:00\n• <b>Шапагат (каз)</b>: Пн, Ср 19:00, Сб 17:00\n• <b>Чайхана (Новички)</b>: Вс 11:00\n• <b>Женский клуб</b>: Вс 13:00',
        "alm_zenk": "🏢 <b>Зенкова 24 (Дом Офицеров)</b>\n\n• <b>8 марта</b>: Ежедневно 19:00, Вт/Чт 12:00\n• <b>АлмА (Женская)</b>: Сб 12:00\n• <b>ААА (Мужская)</b>: Сб 17:00\n• <b>ВДА</b>: уточнять по контактам",
        "alm_tim": "🏢 <b>Тимирязева 42, корпус 23, каб 102</b>\n\n• <b>Наурыз</b>: Вт, Чт, Пт, Сб 19:00, Вс 15:00",
        "alm_bukhar": "🏢 <b>Бухар Жырау 66, 3 этаж</b>\n\n• <b>Друзья Билла</b>: Вт, Чт 12:00-13:00\n• Тел: +7 747-563-75-87",
        "alm_kaskelen": "🏢 <b>ТД «Нур-Жанат» (г. Каскелен)</b>\n\n• <b>Группа «Туран»</b>: Пн, Ср, Сб 17:00–18:15",
        "alm_other": "📍 <b>Другие локации Алматы</b>\n\n• <b>Аксай</b> (Райымбека 493): Вс 13:00\n• <b>НОВЫЕ ОЧКИ</b> (Жибек Жолы 64): Пн, Ср, Пт 19:00, Сб 14:00\n• <b>Боралдай</b> (Курчатова 13а): Сб 17:00"
    },
    "Астана": {
        "ast_petrov": "🏢 <b>ул. Петрова 14/3</b>\n\n• <b>51 параллель</b>: Ср 19:00-20:15; Сб 15:00-16:15\n• <b>Свобода</b>: Пн, Чт, Пт 19:00-20:00\n• <b>Есиль (каз)</b>: Вс 17:00-18:30",
        "ast_other": "📍 <b>Другие локации Астаны</b>\n\n• <b>Большая перемена</b>: Пн, Пт 19:00-20:00\n• <b>Сана</b>: Вт, Чт 20:00-21:15\n• <b>Путь</b>: Вт, Ср, Чт 19:00-20:15\n• <b>Возрождение</b>: Вт 19:00-20:15"
    }
}

# --- КЭШ ДЛЯ ОСТАЛЬНЫХ ГОРОДОВ ---
CACHED_DATA = None

def get_schedule_data():
    global CACHED_DATA
    if CACHED_DATA:
        return CACHED_DATA

    try:
        url = "https://aaorg.kz/sobraniya/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        data = {}
        current_city = "Другое"
        
        IGNORE_WORDS = ["Где проходят", "Контакты", "Собрания", "Онлайн", "Список", "Вопросы", "Главная", "Новости", "Алматы", "Астана"]

        for el in soup.find_all(['h2', 'h3', 'p']):
            text = el.text.strip()
            if not text: continue
            
            if el.name == 'h2':
                if any(word.lower() in text.lower() for word in IGNORE_WORDS):
                    continue
                current_city = text.replace('Группы в ', '').replace('Группы ', '').strip()
                if current_city not in data: 
                    data[current_city] = []
                
            elif el.name == 'h3':
                group_name = text
                next_p = el.find_next_sibling('p')
                info = ""
                if next_p:
                    info = next_p.text.replace("Адрес:", "\n📍 Адрес:").replace("Время:", "\n⏰ Время:").replace("Контакты:", "\n📞 Контакты:")
                
                if current_city in data:
                    data[current_city].append(f"• <b>{group_name}</b>{info}")
        
        if "Онлайн" not in data:
            data["Онлайн"] = ["• <b>Пробуждение</b>: Вт, Чт, Сб 21:00\n<a href='https://us06web.zoom.us/j/82036099070'>Zoom</a> | Пароль: +77754565358"]

        CACHED_DATA = data
        return data
    except Exception as e:
        logging.error(f"Ошибка парсинга: {e}")
        return {}

def get_cities_kb(lang="ru"):
    data = get_schedule_data()
    kb = []
    
    # Добавляем Алматы и Астану вручную в начало списка
    kb.append([
        InlineKeyboardButton(text="🏙 Алматы", callback_data="s_hard_Алматы"),
        InlineKeyboardButton(text="🏙 Астана", callback_data="s_hard_Астана")
    ])
    
    row = []
    for city in sorted(data.keys()):
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
    
    data = get_schedule_data()
    if not data:
        await message.answer("Сайт с расписанием временно недоступен. Попробуйте позже.")
        return
        
    await message.answer(
        TEXTS[lang]["title"],
        reply_markup=get_cities_kb(lang),
        parse_mode="HTML",
    )

@router.callback_query(F.data.startswith("s_"))
async def callback_schedule(callback: types.CallbackQuery):
    data = callback.data
    lang = await get_user_language(callback.from_user.id)
    if not lang: lang = "ru"
    t = TEXTS[lang]

    if data == "s_back":
        await callback.message.edit_text(t["title"], reply_markup=get_cities_kb(lang), parse_mode="HTML")
        await callback.answer()
        return

    # --- ОБРАБОТКА АЛМАТЫ И АСТАНЫ ---
    if data.startswith("s_hard_"):
        city = data.replace("s_hard_", "")
        kb = []
        for key, text in HARDCODED_CITIES[city].items():
            kb.append([InlineKeyboardButton(text=text.split('<b>')[1].split('</b>')[0], callback_data=f"s_display_{key}")])
        kb.append([InlineKeyboardButton(text=t["back"], callback_data="s_back")])
        await callback.message.edit_text(f"🏙 <b>{city}</b>\nВыберите группу:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")
        await callback.answer()
        return

    if data.startswith("s_display_"):
        key = data.replace("s_display_", "")
        for city_data in HARDCODED_CITIES.values():
            if key in city_data:
                text = city_data[key] + t["help_text"]
                kb = [[InlineKeyboardButton(text=t["back"], callback_data="s_back")]]
                await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")
                await callback.answer()
                return

    # --- ОБРАБОТКА ОСТАЛЬНЫХ ГОРОДОВ ---
    elif data.startswith("s_"):
        city_name = data.replace("s_", "")
        parsed_data = get_schedule_data()
        groups = parsed_data.get(city_name)
        
        if not groups:
            await callback.answer(t["no_schedule"], show_alert=True)
            return
            
        text = f"🏙 <b>{city_name}</b>\n\n" + "\n\n".join(groups) + t["help_text"]
        kb = [[InlineKeyboardButton(text=t["back"], callback_data="s_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

    await callback.answer()