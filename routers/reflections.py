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
        
        # Находим блок с контентом (на mos-nach это обычно основной контейнер #content или #main)
        content_block = soup.find(id='content') or soup.find(id='main') or soup.find('article')
        
        if content_block:
            # Ищем заголовок дня (дата + название)
            title_element = content_block.find('h1', class_='entry-title') or content_block.find('h1') or content_block.find('h2')
            title_text = title_element.get_text(strip=True) if title_element else "Ежедневное размышление"
            
            # Собираем все абзацы текста
            paragraphs = [p.get_text(strip=True) for p in content_block.find_all('p') if p.get_text(strip=True)]
            
            # Фильтруем технический мусор сайта внизу страницы
            clean_paragraphs = []
            for p in paragraphs:
                if any(word in p for word in ["Посмотреть размышления", "Архив размышлений", "Предыдущее", "Следующее", "Перейти к"]):
                    continue
                clean_paragraphs.append(p)

            if len(clean_paragraphs) >= 3:
                # На сайте mos-nach структура обычно такая:
                # 0 - Дата/заголовок (иногда дублируется)
                # 1 - Цитата Билла
                # 2 - Источник (книга, страница)
                # Остальное - размышление
                
                # Проверим, не дублирует ли первый абзац заголовок h1
                start_idx = 0
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
                # Если абзацев мало, выводим всё как один сплошной текст
                main_text = "\n\n".join(clean_paragraphs)
                text = f"📘 **{title_text}**\n\n{main_text}"
        else:
            # Если вообще не нашли блоков контента, собираем текст по всем параграфам страницы
            paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
            if paragraphs:
                text = "📘 **Ежедневное размышление**\n\n" + "\n\n".join(paragraphs[:8]) # Первые 8 абзацев
            else:
                raise Exception("Не удалось найти текстовые блоки на странице")

        await waiting_message.delete()
        
        # Если текст получился слишком длинным для Markdown, отправляем как обычный текст
        try:
            await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception:
            await message.answer(text.replace("**", "").replace("_*", "").replace("_", ""), disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"Ошибка парсинга с mos-nach.ru: {e}")
        await waiting_message.delete()
        await message.answer(
            f"⚠️ Бот зашел на сайт, но структура страницы изменилась.\n"
            f"Ты можешь прочесть размышление по прямой ссылке:\n\n🔗 [Читать на mos-nach.ru]({url})",
            parse_mode="Markdown"
        )