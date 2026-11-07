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

CACHED_DATA = None

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
        
        # Ищем ВСЕ заголовки и блоки с группами
        for el in soup.find_all(['h2', 'h3']):
            # Если это заголовок города (h2)
            if el.name == 'h2':
                text = el.text.strip()
                if "Где проходят" in text or "Выбери свою" in text or not text:
                    continue
                current_city = text
                if current_city not in data:
                    data[current_city] = []
            
            # Если это группа (h3)
            elif el.name == 'h3':
                if not current_city:
                    continue
                
                group_name = el.text.strip()
                
                # Ищем следующий параграф (описание группы)
                next_p = el.find_next('p')
                info = ""
                if next_p:
                    info = next_p.text.replace("Адрес:", "\n📍 Адрес:").replace("Время:", "\n⏰ Время:").replace("Контакты:", "\n📞 Контакты:").replace("Площадка Zoom:", "\n💻 Zoom:").replace("Пароль по номеру:", "\n🔑 Пароль:").replace("Чат в Whatsapp:", "\n💬 WhatsApp:").replace("Чат в Telegram:", "\n💬 Telegram:").strip()
                
                if current_city and current_city in data:
                    data[current_city].append(f"• <b>{group_name}</b>{info}")

        # Очищаем пустые города
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
    
    # Скачиваем данные при запросе (один раз)
    import asyncio
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
        await callback.message.edit_text(t["title"], reply_markup=get_cities_kb(CACHED_DATA, lang), parse_mode="HTML")
        await callback.answer()
        return

    elif data_str.startswith("s_"):
        city_name = data_str.replace("s_", "")
        groups = CACHED_DATA.get(city_name) if CACHED_DATA else None
        
        if not groups:
            await callback.answer(t["no_schedule"], show_alert=True)
            return
            
        text = f"🏙 <b>{city_name}</b>\n\n" + "\n\n".join(groups) + t["help_text"]
        
        if len(text) > 4000:
            chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
            
            for chunk in chunks:
                await callback.bot.send_message(callback.from_user.id, chunk, parse_mode="HTML")
            
            kb = [[InlineKeyboardButton(text=t["back"], callback_data="s_back")]]
            await callback.bot.send_message(callback.from_user.id, "Выберите действие:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
            
        else:
            kb = [[InlineKeyboardButton(text=t["back"], callback_data="s_back")]]
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

    await callback.answer()