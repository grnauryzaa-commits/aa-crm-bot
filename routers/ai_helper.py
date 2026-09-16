import os
import aiohttp
from services.knowledge_base import find_canonical_context
from database import add_message_to_history, get_recent_history

async def ask_ai_for_beginner(user_id: int, user_message: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "Алкоголь умеет нас изолировать, но сейчас ты можешь сделать вдох и обратиться к живому другу по программе."

    # 1. Сохраняем сообщение пользователя в историю
    await add_message_to_history(user_id, "user", user_message)

    # 2. Ищем канонический текст по базе знаний
    canonical_text = find_canonical_context(user_message)
    context_instruction = ""
    if canonical_text:
        context_instruction = (
            f"\n\nЖЕСТКИЙ КАНОН АА (ИСПОЛЬЗУЙ ИМЕННО ЭТОТ ТЕКСТ БЕЗ ИЗМЕНЕНИЙ):\n"
            f"{canonical_text}\n"
            f"Строго опирайся на этот канон, не придумывай правила от себя и не путай формулировки."
        )

    # 3. Подгружаем недавнюю историю диалога
    history = await get_recent_history(user_id, limit=6)

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "Ты — опытный член сообщества Анонимных Алкоголиков (АА) в Казахстане. "
        "Твоя задача — тепло, просто и с пониманием отвечать новичку.\n\n"
        "ПРАВИЛА:\n"
        "1. Если передан ЖЕСТКИЙ КАНОН АА, бери точный текст оттуда и объясняй его простыми словами.\n"
        "2. Говори как живой старший товарищ: 4–7 предложений, без менторства и нравоучений.\n"
        "3. Никогда не признавайся, что ты бот или искусственный интеллект.\n"
        "4. Напоминай про кнопку «👤 Позвать живого служащего» под сообщением и сайт aaorg.kz для расписания."
        f"{context_instruction}"
    )

    messages = [{"role": "system", "content": system_prompt}] + history

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": messages,
        "temperature": 0.05,
        "max_tokens": 600
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