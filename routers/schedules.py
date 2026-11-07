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

# --- КЭШ ---
CACHED_DATA = None

def get_schedule_data():
    global CACHED_DATA
    if CACHED_DATA:
        return CACHED_DATA

    try:
        url = "https://aaorg.kz/sobraniya/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        data = {}
        current_city = None
        
        # Ищем все заголовки городов (h2) и блоки с группами (div)
        for el in soup.find_all(['h2', 'div']):
            
            # 1. Если нашли заголовок города (h2)
            if el.name == 'h2':
                text = el.text.strip()
                if "Где проходят" in text or "Выбери свою" in text or not text:
                    continue
                
                current_city = text
                if current_city not in data:
                    data[current_city] = []
            
            # 2. Если нашли блок с информацией о группе
            elif el.name == 'div' and 'elementor-image-box-content' in el.get('class', []):
                if not current_city:
                    continue
                
                # Ищем ВНУТРИ этого блока строго h3 (название) и строго p (описание)
                h3 = el.find('h3')
                p = el.find('p')
                
                if h3 and p:
                    group_name = h3.text.strip()
                    info = p.text.replace("Адрес:", "\n📍 Адрес:").replace("Время:", "\n⏰ Время:").replace("Контакты:", "\n📞 Контакты:").replace("Площадка Zoom:", "\n💻 Zoom:").replace("Пароль по номеру:", "\n🔑 Пароль:").replace("Чат в Whatsapp:", "\n💬 WhatsApp:").replace("Чат в Telegram:", "\n💬 Telegram:").strip()
                    
                    data[current_city].append(f"• <b>{group_name}</b>{info}")

        # Удаляем пустые города
        data = {k: v for k, v in data.items() if v}
        
        CACHED_DATA = data
        return data
    except Exception as e:
        logging.error(f"Ошибка парсинга: {e}")
        return {}

def get_cities_kb(lang="ru"):
    data = get_schedule_data()
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

    elif data.startswith("s_"):
        city_name = data.replace("s_", "")
        parsed_data = get_schedule_data()
        groups = parsed_data.get(city_name)
        
        if not groups:
            await callback.answer(t["no_schedule"], show_alert=True)
            return
            
        # Формируем текст: Заголовок города + список групп + помощь
        text = f"🏙 <b>{city_name}</b>\n\n" + "\n\n".join(groups) + t["help_text"]
        
        # Защита от слишком длинных сообщений (Алматы - очень большой город)
        if len(text) > 4000:
            text = text[:4000] + "..."
            
        kb = [[InlineKeyboardButton(text=t["back"], callback_data="s_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

    await callback.answer()