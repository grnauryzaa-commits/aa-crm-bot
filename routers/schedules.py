from aiogram import F, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_user_language
import requests
from bs4 import BeautifulSoup
import logging
import asyncio

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
        
        # Находим все заголовки городов
        h2_tags = soup.find_all('h2')
        
        for i, h2 in enumerate(h2_tags):
            city_name = h2.text.strip()
            if "Где проходят" in city_name or "Выбери свою" in city_name or not city_name:
                continue
            
            # Определяем границы секции для этого города
            start = h2
            end = h2_tags[i+1] if i + 1 < len(h2_tags) else None
            
            data[city_name] = []
            
            # Ищем все группы (h3) внутри этой секции
            current = start.find_next_sibling()
            while current and current != end:
                # Ищем h3 на текущем уровне
                for h3 in current.find_all('h3'):
                    group_name = h3.text.strip()
                    
                    # Для каждой группы ищем ближайший p
                    p = h3.find_next('p')
                    info = ""
                    if p:
                        info = p.text.replace("Адрес:", "\n📍 Адрес:").replace("Время:", "\n⏰ Время:").replace("Контакты:", "\n📞 Контакты:").replace("Площадка Zoom:", "\n💻 Zoom:").replace("Пароль по номеру:", "\n🔑 Пароль:").replace("Чат в Whatsapp:", "\n💬 WhatsApp:").replace("Чат в Telegram:", "\n💬 Telegram:").strip()
                    
                    data[city_name].append(f"• <b>{group_name}</b>{info}")
                
                current = current.find_next_sibling()
        
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