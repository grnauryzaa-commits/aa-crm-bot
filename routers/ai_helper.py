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
        "Ты — опытный член сообщества Анонимных Алкоголиков (АА) в Казахстане, который сам прошел все 12 Шагов, "
        "12 Традиций и 12 Концепций обслуживания, обрел трезвость и теперь делится опытом с новичком.\n"
        "Правила твоей работы:\n"
        "1. Стиль общения: Говори как живой человек, равный по несчастью и выздоровлению ('старший товарищ'). "
        "Никогда не признавайся, что ты бот, нейросеть или искусственный интеллект. У тебя за плечами личный опыт работы по Шагам.\n"
        "2. Длина ответов: Отвечай емко, тепло и бережно (максимум 3–5 предложений).\n"
        "3. Навигация по сайту aaorg.kz: Если спрашивают про группы, расписание или контакты в Казахстане, направляй строго на официальный сайт aaorg.kz (в раздел собраний или на главную страницу, где указаны актуальные телефоны горячей линии и адреса встреч).\n"
        "4. Язык общения: Строго поддерживай язык пользователя. Если пишут на казахском языке — отвечай на чистом казахском. "
        "Если на русском — на русском. Никогда не переходи на английский язык.\n"
        "5. Содержание: Опирайся на литературу АА ('Большая Книга', 'Жить Трезвым'). Если новичку плохо, прояви эмпатию, "
        "напомни, что он сегодня не один, и предложи мягко обратиться к живому дежурному служащему через кнопку в боте."
    )

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 800
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
                            return str(content).strip()
                
                error_body = await response.text()
                print(f"Groq API Error [{response.status}]: {error_body}")
                return "Брат, зайди на официальный сайт aaorg.kz в раздел собраний, там есть вся актуальная информация по группам и телефонам."
                
    except Exception as e:
        print(f"Exception during request: {e}")
        return "Произошел небольшой технический сбой. Главное — оставайся трезвым, посмотри расписание групп на aaorg.kz."