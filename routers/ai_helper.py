import os
import aiohttp
from services.knowledge_base import find_canonical_context
from database import add_message_to_history, get_recent_history, get_user_language

async def ask_ai_for_beginner(user_id: int, user_message: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "Алкоголь умеет нас изолировать, но сейчас ты можешь сделать вдох и обратиться к живому другу по программе."

    # 1. Сохраняем сообщение пользователя в историю
    await add_message_to_history(user_id, "user", user_message)

    # 2. Ищем точный канонический текст по нашей базе знаний
    canonical_text = find_canonical_context(user_message)
    
    # ЕСЛИ КАТЕГОРИЯ НАЙДЕНА: возвращаем её НАПРЯМУЮ, минуя ИИ-галлюцинации!
    if canonical_text:
        bot_reply = (
            f"{canonical_text}\n\n"
            f"Если хочешь узнать больше или обсудить это, нажми кнопку «👤 Позвать живого служащего» под сообщением или зайди на aaorg.kz."
        )
        await add_message_to_history(user_id, "assistant", bot_reply)
        return bot_reply

    # 3. Определяем язык пользователя (по умолчанию 'ru')
    lang = get_user_language(user_id)
    lang_instruction = (
        "Отвечай строго на казахском языке. (Қазақ тілінде жауап бер.)" 
        if lang == 'kk' 
        else "Отвечай строго на русском языке."
    )

    # 4. Если это общий вопрос, идем в Groq с учетом языка пользователя
    history = await get_recent_history(user_id, limit=6)

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "Ты — опытный член сообщества Анонимных Алкоголиков (АА) в Казахстане. "
        "Твоя задача — давать исключительно правдивые ответы по программе АА.\n\n"
        f"{lang_instruction}\n\n"
        "ПРАВИЛА:\n"
        "1. Говори тепло, по-дружески (4–7 предложений).\n"
        "2. Никогда не признавайся, что ты бот.\n"
        "3. Если тебя спрашивают про источники, ссылайся только на Большую Книгу АА, книгу «Двенадцать Шагов и Двенадцать Традиций» и сайт aaorg.kz. Никогда не выдумывай сторонние мануалы.\n"
        "4. Всегда направляй на сайт aaorg.kz и напоминай про кнопку «👤 Позвать живого служащего»."
    )

    messages = [{"role": "system", "content": system_prompt}] + history

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": messages,
        "temperature": 0.01,
        "max_tokens": 400
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content")
                        if content:
                            bot_reply = str(content).strip()
                            await add_message_to_history(user_id, "assistant", bot_reply)
                            return bot_reply
                
                error_body = await response.text()
                print(f"Groq API Error [{response.status}]: {error_body}")
                return "Я внимательно тебя слушал, но на секунду отвлекся. Если вопрос срочный, нажми кнопку связи с дежурным ниже."
                
    except Exception as e:
        print(f"Exception during AI request: {e}")
        return "Произошел небольшой технический сбой. Главное — оставайся трезвым, посмотри расписание групп на aaorg.kz."