from aiogram import Router, F, types, Bot
import aiohttp
from bs4 import BeautifulSoup
import logging

router = Router()

# Универсальная и надежная функция-парсер
async def get_reflection_text():
    url = "https://mos-nach.ru/thinks/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=15) as response:
                if response.status != 200:
                    logging.error(f"Сайт вернул статус {response.status}")
                    return None
                html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        
        # Шаг 1: Пытаемся найти заголовок
        title_element = soup.find('h1', class_='entry-title') or soup.find('h1') or soup.find('h2')
        title_text = title_element.get_text(strip=True) if title_element else "Ежедневное размышление"
        
        # Шаг 2: Ищем контентный блок. Если его нет — берем все параграфы со страницы
        content_block = soup.find(id='content') or soup.find(id='main') or soup.find('article') or soup.find('main')
        if content_block:
            paragraphs = [p.get_text(strip=True) for p in content_block.find_all('p') if p.get_text(strip=True)]
        else:
            paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]

        if not paragraphs:
            logging.error("На странице вообще не найдено тегов <p>")
            return None

        # Шаг 3: Фильтруем текст от технического мусора внизу страницы
        clean_paragraphs = []
        for p in paragraphs:
            stop_words = [
                "место под альтернативный", 
                "издание было подготовлено", 
                "alcoholics anonymous", 
                "анонимные алкоголики ©",
                "посмотреть размышления",
                "архив размышлений",
                "предыдущее",
                "следующее"
            ]
            if any(word in p.lower() for word in stop_words):
                break
            clean_paragraphs.append(p)

        # Шаг 4: Форматируем собранный текст
        if len(clean_paragraphs) >= 3:
            start_idx = 0
            # Если первый абзац дублирует заголовок, сдвигаем индекс
            if title_text.lower() in clean_paragraphs[0].lower() or len(clean_paragraphs[0]) < 12:
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
        else:
            # Если абзацев мало, просто объединяем всё, что нашли
            main_text = "\n\n".join(clean_paragraphs)
            return f"📘 **{title_text}**\n\n{main_text}"

    except Exception as e:
        logging.error(f"Ошибка при парсинге: {e}")
        return None

# Хэндлер для кнопки в боте
@router.message(F.text == "📘 Ежедневные размышления")
async def show_reflections(message: types.Message):
    waiting_message = await message.answer("🔄 Загружаю сегодняшнее размышление...")
    text = await get_reflection_text()
    await waiting_message.delete()
    
    if text:
        try:
            await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception:
            # На случай, если в тексте попадутся спецсимволы, ломающие Markdown
            clean_text = text.replace("**", "").replace("_*", "").replace("_", "")
            await message.answer(clean_text, disable_web_page_preview=True)
    else:
        await message.answer(
            "⚠️ Не удалось автоматически скопировать текст с сайта.\n"
            "Ты можешь прочесть его по прямой ссылке:\n\n"
            "🔗 [Перейти на mos-nach.ru](https://mos-nach.ru/thinks/)", 
            parse_mode="Markdown"
        )

# Функция автоматической отправки в канал по таймеру
async def send_daily_reflection_to_channel(bot: Bot):
    # ⚠️ НЕ ЗАБУДЬТЕ УКАЗАТЬ ТЕГ ВАШЕГО КАНАЛА НАУРЫЗ С СИМВОЛОМ @
    CHANNEL_ID = "@твой_канал_наурыз" 
    
    logging.info("Запуск автоматической отправки размышлений в канал...")
    text = await get_reflection_text()
    
    if text:
        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="Markdown", disable_web_page_preview=True)
            logging.info("Размышление успешно отправлено в канал!")
        except Exception as e:
            try:
                clean_text = text.replace("**", "").replace("_*", "").replace("_", "")
                await bot.send_message(chat_id=CHANNEL_ID, text=clean_text, disable_web_page_preview=True)
            except Exception as ex:
                logging.error(f"Не удалось отправить сообщение в канал: {ex}")
    else:
        logging.error("Сайт не отдал текст для автоматической рассылки.")