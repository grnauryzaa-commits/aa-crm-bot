import os
import aiohttp
from services.knowledge_base import find_canonical_context
from database import add_message_to_history, get_recent_history

async def ask_ai_for_beginner(user_id: int, user_message: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "Алкоголь умеет нас изолировать, но сейчас ты можешь сделать вдох и обратиться к живому другу по программе."

    # 1. Сохраняем сообщение
    await add_message_to_history(user_id, "user", user_message)

    # 2. Ищем канонический текст по RAG (это самое надежное)
    canonical_text = find_canonical_context(user_message)
    context_instruction = ""
    if canonical_text:
        context_instruction = (
            f"\n\nОБЯЗАТЕЛЬНЫЙ КАНОН ДЛЯ ЭТОГО ОТВЕТА:\n"
            f"\"{canonical_text}\"\n"
            f"Используй эту формулировку точно, не искажай и не путай номера шагов или традиций."
        )

    history = await get_recent_history(user_id, limit=6)

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Компактный, но жесткий промпт, который не перегружает модель
    system_prompt = (
        "Ты — опытный член сообщества Анонимных Алкоголиков (АА) в Казахстане, прошедший 12 Шагов и Традиций. "
        "Твоя задача — тепло и с пониманием отвечать новичку, строго опираясь на литературу АА.\n\n"
        "ПРАВИЛА:\n"
        "1. Четко разделяй Шаги (1-12), Традиции (1-12) и Концепции. Никогда не путай их номера и суть.\n"
        "2. Если сомневаешься в номере или тексте традиции/шага — отвечай кратко и направляй к спонсору или на кнопку связи.\n"
        "3. Стиль: живой старший товарищ, 4–7 предложений, без менторства и заумных фраз.\n"
        "4. Никогда не признавайся, что ты бот или ИИ. Поддерживай язык пользователя (русский/казахский).\n"
        "5. Напоминай про кнопку «👤 Позвать живого служащего» под сообщением и сайт aaorg.kz для расписания."
        f"{context_instruction}"
    )

    messages = [{"role": "system", "content": system_prompt}] + history

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 600  # Снижаем лимит токенов, чтобы ответ генерировался быстрее и без сбоев таймаута
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
        print(f"Exception during request: {e}")
        return "Произошел небольшой технический сбой. Главное — оставайся трезвым, посмотри расписание групп на aaorg.kz."