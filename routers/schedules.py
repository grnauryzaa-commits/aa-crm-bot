from aiogram import F, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_user_language
import requests
from bs4 import BeautifulSoup
import logging
import asyncio
import re

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

CACHED_DATA = None

def clean_text(text):
    """Убирает все HTML-теги из текста"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace("&lt;", "").replace("&gt;", "").replace("&amp;", "&").replace("&lt;/b", "")
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'(\d)([А-ЯЁA-Z])', r'\1 \2', text)
    return text.strip()

def fetch_schedule_sync():
    global CACHED_DATA
    if CACHED_DATA:
        return CACHED_DATA

    url = "https://aaorg.kz/sobraniya/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        data = {}
        current_city = None
        current_group_name = None
        current_info = []
        
        for el in soup.find_all(['h2', 'h3', 'p']):
            if el.name == 'h2':
                if current_city and current_group_name:
                    info_text = clean_text("\n".join(current_info))
                    # Используем символ "•" вместо HTML-тега <b>
                    data[current_city].append(f"🔹 {clean_text(current_group_name)}\n{info_text}")
                
                text = el.text.strip()
                if "Где проходят" in text or "Выбери свою" in text or not text:
                    current_city = None
                    continue
                
                current_city = text.capitalize()
                current_group_name = None
                current_info = []
                if current_city not in data:
                    data[current_city] = []
            
            elif el.name == 'h3':
                if not current_city:
                    continue
                
                if current_group_name:
                    info_text = clean_text("\n".join(current_info))
                    data[current_city].append(f"🔹 {clean_text(current_group_name)}\n{info_text}")
                
                current_group_name = el.text.strip()
                current_info = []
            
            elif el.name == 'p':
                if not current_city or not current_group_name:
                    continue
                
                text = el.text.strip()
                if any(word in text for word in ["Адрес", "Время", "Контакты", "Zoom", "Пароль", "Телефон", "Как нас найти", "Формат", "Telegram", "WhatsApp"]):
                    info = text.replace("Адрес:", "📍 Адрес:").replace("Время:", "⏰ Время:").replace("Контакты:", "📞 Контакты:").replace("Площадка Zoom:", "💻 Zoom:").replace("Пароль по номеру:", "🔑 Пароль:").replace("Чат в Whatsapp:", "💬 WhatsApp:").replace("Чат в Telegram:", "💬 Telegram:").replace("2Gis:", "📍 2GIS:")
                    current_info.append(info)

        if current_city and current_group_name:
            info_text = clean_text("\n".join(current_info))
            data[current_city].append(f"🔹 {clean_text(current_group_name)}\n{info_text}")

        data = {k: v for k, v in data.items() if v}
        CACHED_DATA = data
        return data
    except Exception as e:
        logging.error(f"Ошибка парсинга: {e}")
        return {}

def get_cities_kb(data, lang="ru"):
    kb = []
    row = []
    cities = sorted(data.keys())
    
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
    
    data = await asyncio.to_thread(fetch_schedule_sync)
    
    if not data:
        await message.answer("Сайт с расписанием временно недоступен. Попробуйте позже.")
        return
        
    await message.answer(
        TEXTS[lang]["title"],
        reply_markup=get_cities_kb(data, lang),
        parse_mode="HTML",
    )

@router.callback_query(F.data.startswith("s_"))
async def callback_schedule(callback: types.CallbackQuery):
    data_str = callback.data
    lang = await get_user_language(callback.from_user.id)
    if not lang: lang = "ru"
    t = TEXTS[lang]

    if data_str == "s_back":
        if CACHED_DATA:
            await callback.message.edit_text(t["title"], reply_markup=get_cities_kb(CACHED_DATA, lang), parse_mode="HTML")
        else:
            await callback.answer("Нажмите «Расписание» заново.", show_alert=True)
        await callback.answer()
        return

    elif data_str.startswith("s_"):
        city_name = data_str.replace("s_", "")
        groups = CACHED_DATA.get(city_name) if CACHED_DATA else None
        
        if not groups:
            await callback.answer(t["no_schedule"], show_alert=True)
            return
            
        full_text = f"🏙 {city_name}\n\n" + "\n\n".join(groups) + t["help_text"]
        
        # Отправляем ОДНИМ сообщением, но БЕЗ parse_mode="HTML", 
        # чтобы Telegram вообще не пытался искать теги и падать
        if len(full_text) > 4000:
            # Если текст реально огромный (бывает у Алматы), режем по 4000, но уже без риска
            chunks = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
            for chunk in chunks:
                await callback.bot.send_message(callback.from_user.id, chunk)
        else:
            await callback.bot.send_message(callback.from_user.id, full_text)
            
        kb = [[InlineKeyboardButton(text=t["back"], callback_data="s_back")]]
        await callback.bot.send_message(callback.from_user.id, "Выберите действие:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

    await callback.answer()