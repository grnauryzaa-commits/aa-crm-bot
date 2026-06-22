from aiogram import Router, F, types, Bot
import aiohttp
from bs4 import BeautifulSoup
import logging

router = Router()

# Функция-парсер, которая просто собирает текст с сайта
async def get_reflection_text():
    url = "https://mos-nach.ru/thinks/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return None
                html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        content_block = soup.find(id='content') or soup.find(id='main') or soup.find('article')
        
        if content_block:
            title_element = content_block.find('h1', class_='entry-title') or content_block.find('h1') or content_block.find('h2')
            title_text = title_element.get_text(strip=True) if title_element else "Ежедневное размышление"
            paragraphs = [p.get_text(strip=True) for p in content_block.find_all('p') if p.get_text(strip=True)]
            
            clean_paragraphs = []
            for p in paragraphs:
                if any(word in p.lower() for word in ["место под альтернативный", "издание было подготовлено", "alcoholics anonymous", "анонимные алкоголики ©", "посмотреть размышления", "архив размышлений"]):
                    break
                clean_paragraphs.append(p)

            if len(clean_paragraphs) >= 3:
                start_idx = 0
                if title_text.lower() in clean_paragraphs[0].lower() or len(clean_paragraphs[0]) < 10:
                    start_idx = 1
                quote = clean_paragraphs[start_idx]
                source = clean_paragraphs[start_idx + 1] if (start_idx + 1) < len(clean_paragraphs) else ""
                main_text = "\n\n".join(clean_paragraphs[start_idx + 2:])
                
                return (
                    f"📘 **{title_text}**\n\n"
                    f"«{quote}»\n"
                    f"_* {source}_\n\n"
                    f"{main_text}"
                )
        return None
    except Exception as e:
        logging.error(f"Ошибка при парсинге для рассылки: {e}")
        return None

# Хэндлер для кнопки в самом боте (остался без изменений)
@router.message(F.text == "📘 Ежедневные размышления")
async def show_reflections(message: types.Message):
    waiting_message = await message.answer("🔄 Загружаю сегодняшнее размышление...")
    text = await get_reflection_text()
    await waiting_message.delete()
    
    if text:
        try:
            await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception:
            await message.answer(text.replace("**", "").replace("_*", "").replace("_", ""), disable_web_page_preview=True)
    else:
        await message.answer("⚠️ Не удалось загрузить текст. [Перейти на сайт](https://mos-nach.ru/thinks/)", parse_mode="Markdown")

# ФУНКЦИЯ ДЛЯ АВТОМАТИЧЕСКОЙ ОТПРАВКИ В КАНАЛ
async def send_daily_reflection_to_channel(bot: Bot):
    # ⚠️ ЗАМЕНИТЕ НА ТЕГ ВАШЕГО КАНАЛА (ОБЯЗАТЕЛЬНО С @) ИЛИ ЕГО ID
    CHANNEL_ID = "@aa_nauryz" 
    
    logging.info("Запуск автоматической отправки размышлений в канал...")
    text = await get_reflection_text()
    
    if text:
        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="Markdown", disable_web_page_preview=True)
            logging.info("Размышление успешно отправлено в канал!")
        except Exception as e:
            # Если упало из-за разметки, шлем чистым текстом
            try:
                clean_text = text.replace("**", "").replace("_*", "").replace("_", "")
                await bot.send_message(chat_id=CHANNEL_ID, text=clean_text, disable_web_page_preview=True)
            except Exception as ex:
                logging.error(f"Не удалось отправить сообщение в канал: {ex}")