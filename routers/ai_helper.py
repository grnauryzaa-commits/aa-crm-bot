import os
import aiohttp
from services.knowledge_base import find_canonical_context
from database import add_message_to_history, get_recent_history

async def ask_ai_for_beginner(user_id: int, user_message: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "Алкоголь умеет нас изолировать, но сейчас ты можешь сделать вдох и обратиться к живому другу по программе."

    # 1. Сохраняем входящее сообщение пользователя в базу истории
    await add_message_to_history(user_id, "user", user_message)

    # 2. Ищем канонический текст по RAG
    canonical_text = find_canonical_context(user_message)
    context_instruction = ""
    if canonical_text:
        context_instruction = (
            f"\n\nОБЯЗАТЕЛЬНЫЙ ИСТОЧНИК ПРАВДЫ ДЛЯ ЭТОГО СООБЩЕНИЯ:\n"
            f"Пользователь спрашивает о конкретном принципе АА. Вот официальная формулировка из литературы, которую ты ДОЛЖЕН подтвердить и использовать:\n"
            f"\"{canonical_text}\"\n"
            f"Не искажай её, не путай с другими шагами и объясняй строго опираясь на неё."
        )

    # 3. Загружаем последние 6 сообщений из истории диалога
    history = await get_recent_history(user_id, limit=6)

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "Ты — опытный член сообщества Анонимных Алкоголиков (АА) в Казахстане, который сам прошел все 12 Шагов, "
        "12 Традиций и 12 Концепций обслуживания, обрел трезвость и теперь делится опытом с новичком.\n\n"
        "ПРАВИЛА ТВОЕЙ РАБОТЫ:\n"
        "1. Стиль и грамотность: Говори как живой, теплый и понимающий старший товарищ. Отвечай подробно и душевно (4–7 предложений), объясняя суть вещей простыми словами. Пиши строго без орфографических и стилистических ошибок. Никогда не признавайся, что ты бот или нейросеть.\n"
        "2. Язык: Строго поддерживай язык пользователя (русский или казахский). Никогда не переходи на английский.\n"
        "3. ЗАПРЕТ НА СПОРЫ: Если пользователь указывает на ошибку, немедленно извинись, признай её и сверься с каноном.\n"
        "4. Интерфейс и кнопка связи: Под каждым твоим сообщением в боте ВСЕГДА находится инлайн-кнопка «👤 Позвать живого служащего». Никогда не утверждай, что в АА нет кнопок или что связь с дежурным устроена как-то иначе. Если человеку нужна помощь живого человека, прямо направь его нажать на эту кнопку под сообщением.\n"
        "5. Контакты и сайты: Если спрашивают про группы или расписание, тепло направляй на официальный сайт aaorg.kz (в раздел собраний). Никогда не выдумывай номера телефонов!\n"
        "6. Учитывай контекст предыдущих сообщений из истории, не переспрашивай то, о чем пользователь уже говорил."
        f"{context_instruction}"
    )

    # Передаем системный промпт, затем всю историю диалога
    messages = [{"role": "system", "content": system_prompt}] + history

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1000
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
                            # 4. Сохраняем ответ бота в историю
                            await add_message_to_history(user_id, "assistant", bot_reply)
                            return bot_reply
                
                error_body = await response.text()
                print(f"Groq API Error [{response.status}]: {error_body}")
                return "Загляни на официальный сайт aaorg.kz в раздел собраний, там найдешь актуальное расписание групп. Если нужна помощь, нажми кнопку связи с дежурным."
                
    except Exception as e:
        print(f"Exception during request: {e}")
        return "Произошел небольшой технический сбой. Главное — оставайся трезвым, посмотри расписание групп на aaorg.kz."