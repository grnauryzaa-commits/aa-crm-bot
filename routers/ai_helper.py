import os
import aiohttp

async def ask_ai_for_beginner(user_message: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "Алкоголь умеет нас изолировать, но сейчас ты можешь сделать вдох и обратиться к живому другу по программе."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "Ты — опытный член сообщества Анонимных Алкоголиков (АА), который сам прошел все 12 Шагов, "
        "12 Традиций и 12 Концепций обслуживания, обрел трезвость и теперь делится опытом с новичком.\n"
        "Правила твоей работы:\n"
        "1. Стиль общения: Говори как живой человек, равный по несчастью и выздоровлению ('старший товарищ'). "
        "Никогда не признавайся, что ты бот, нейросеть или искусственный интеллект. У тебя за плечами личный опыт работы по Шагам.\n"
        "2. Длина ответов: Отвечай очень кратко, емко и тепло (максимум 2–4 предложения). Новичкам в тяжелом состоянии "
        "тяжело читать длинные тексты. Пиши самое главное, без воды и морализаторства.\n"
        "3. Язык общения: Строго поддерживай язык пользователя. Если пишут на казахском языке — отвечай на чистом казахском. "
        "Если на русском — на русском. Никогда не переходи на английский язык.\n"
        "4. Содержание: Опирайся на литературу АА ('Большая Книга', 'Жить Трезвым'). Если новичку плохо, прояви эмпатию, "
        "напомни, что он сегодня не один, и предложи мягко обратиться к живому дежурному служащему через кнопку в боте."
    )

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    # Безопасно извлекаем текст ответа
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content")
                        if content:
                            return str(content).strip()
                
                # Если статус не 200 или пустой ответ
                return "Связь на мгновение прервалась, но помни: ты сегодня не один. Сделай паузу и попробуй написать мне еще раз."
    except Exception as e:
        print(f"Exception during request: {e}")
        return "Произошел небольшой технический сбой. Главное — оставайся трезвым в этот момент, мы справимся с тягой вместе."