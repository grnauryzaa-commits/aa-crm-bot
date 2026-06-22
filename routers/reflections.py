from aiogram import Router, F, types
import aiohttp
from bs4 import BeautifulSoup
import logging

router = Router()

@router.message(F.text == "📘 Ежедневные размышления")
async def show_reflections(message: types.Message):
    waiting_message = await message.answer("🔄 Загружаю сегодняшнее размышление...")

    url = "https://mos-nach.ru/thinks/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    raise Exception(f"Сайт вернул статус код: {response.status}")
                html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        
        # Находим контейнер контента
        content_block = soup.find(id='content') or soup.find(id='main') or soup.find('article')
        
        if content_block:
            # Ищем заголовок дня
            title_element = content_block.find('h1', class_='entry-title') or content_block.find('h1') or content_block.find('h2')
            title_text = title_element.get_text(strip=True) if title_element else "Ежедневное размышление"
            
            # Собираем все абзацы
            paragraphs = [p.get_text(strip=True) for p in content_block.find_all('p') if p.get_text(strip=True)]
            
            # Фильтруем текст, отсекая технический мусор и копирайты внизу страницы
            clean_paragraphs = []
            for p in paragraphs:
                # Маркеры начала «подвала» сайта, после которых полезный текст заканчивается
                stop_words = [
                    "место под альтернативный", 
                    "издание было подготовлено", 
                    "alcoholics anonymous", 
                    "анонимные алкоголики ©",
                    "посмотреть размышления",
                    "архив размышлений"
                ]
                
                # Если встретили любой из стоп-маркеров — прекращаем сбор абзацев вообще
                if any(word in p.lower() for word in stop_words):
                    break
                    
                clean_paragraphs.append(p)

            # Форматируем вывод
            if len(clean_paragraphs) >= 3:
                start_idx = 0
                # Убираем дубль заголовка, если первый абзац совпадает с h1
                if title_text.lower() in clean_paragraphs[0].lower() or len(clean_paragraphs[0]) < 10:
                    start_idx = 1
                
                quote = clean_paragraphs[start_idx]
                source = clean_paragraphs[start_idx + 1] if (start_idx + 1) < len(clean_paragraphs) else ""
                main_text = "\n\n".join(clean_paragraphs[start_idx + 2:])
                
                text = (
                    f"📘 **{title_text}**\n\n"
                    f"«{quote}»\n"
                    f"_* {source}_\n\n"
                    f"{main_text}"
                )
            else:
                main_text = "\n\n".join(clean_paragraphs)
                text = f"📘 **{title_text}**\n\n{main_text}"
        else:
            raise Exception("Не удалось определить контентный блок сайта")

        await waiting_message.delete()
        
        # Безопасная отправка с обработкой ошибок форматирования Markdown
        try:
            await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception:
            await message.answer(text.replace("**", "").replace("_*", "").replace("_", ""), disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"Ошибка парсинга с mos-nach.ru: {e}")
        await waiting_message.delete()
        await message.answer(
            f"⚠️ Ошибка отображения текста.\n"
            f"Ты можешь открыть размышление на сегодня по прямой ссылке:\n\n🔗 [Читать на mos-nach.ru]({url})",
            parse_mode="Markdown"
        )