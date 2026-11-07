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
        "no_schedule": "Для этой группы пока нет расписания."
    },
    "kk": {
        "title": "📅 <b>АА жиналыстарының кестесі</b>\nҚаланы таңдаңыз:",
        "help_text": "\n\nЕгер сұрақтарыңыз болса, көмек керек болса — біз көмектесуге дайынбыз.\n📞 Жедел желі: +7 (707) 433-74-08",
        "back": "⬅️ Артқа",
        "no_schedule": "Бұл топ үшін әзірге кесте жоқ."
    }
}

# --- КЭШ ДЛЯ РАСПИСАНИЯ ---
CACHED_DATA = None

def get_schedule_data():
    global CACHED_DATA
    # Если данные уже скачаны, отдаем их мгновенно
    if CACHED_DATA:
        return CACHED_DATA

    try:
        url = "https://aaorg.kz/sobraniya/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        data = {}
        current_city = "Другое"
        
        # Список слов-исключений (служебные заголовки с сайта)
        IGNORE_WORDS = ["Где проходят", "Контакты", "Собрания", "Онлайн", "Список", "Вопросы", "Главная", "Новости"]

        for el in soup.find_all(['h2', 'h3', 'p']):
            text = el.text.strip()
            if not text: continue
            
            if el.name == 'h2':
                # Если заголовок содержит служебное слово — пропускаем
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
        
        # Принудительно добавляем Онлайн-группы, если их нет на сайте
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
    row = []
    
    # Сортируем города по алфавиту
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