import aiohttp
import logging
from config import GROQ_API_KEY
from database import get_user_language, add_message_to_history, get_recent_history

async def ask_ai_for_beginner(user_id: int, user_message: str) -> str:
    if not GROQ_API_KEY:
        return "Алкоголь умеет нас изолировать, но сейчас ты можешь сделать вдох и обратиться к живому другу по программе."

    await add_message_to_history(user_id, "user", user_message)

    lang = await get_user_language(user_id)
    lang_instruction = (
        "Отвечай строго на казахском языке. (Қазақ тілінде жауап бер.)" 
        if lang == 'kk' 
        else "Отвечай строго на русском языке."
    )

    history = await get_recent_history(user_id, limit=6)

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "Ты — опытный член сообщества Анонимных Алкоголиков (АА) в Казахстане. "
        "Твоя задача — давать исключительно правдивые ответы по программе АА.\n\n"
        f"{lang_instruction}\n\n"
        "ПРАВИЛА:\n"
        "1. Говори тепло, по-дружески (4–7 предложений).\n"
        "2. Никогда не признавайся, что ты бот.\n"
        "3. Если тебя спрашивают про источники, ссылайся только на Большую Книгу АА, книгу «Двенадцать Шагов и Двенадцать Традиций» и сайт aaorg.kz.\n"
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
                return "Я внимательно тебя слушал, но на секунду отвлекся. Если вопрос срочный, нажми кнопку связи с дежурным ниже."
    except Exception as e:
        logging.error(f"Exception during AI request: {e}")
        return "Произошел небольшой технический сбой. Главное — оставайся трезвым, посмотри расписание групп на aaorg.kz."