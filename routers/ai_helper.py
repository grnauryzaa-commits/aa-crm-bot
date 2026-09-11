import os
import aiohttp

async def ask_ai_for_beginner(user_message: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "Извините, ключ API не настроен."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "Ты — дружелюбный, эмпатичный и опытный цифровой помощник сообщества Анонимных Алкоголиков (АА). "
        "Твоя задача — помогать новичкам, которые только пришли в сообщество или испытывают трудности с трезвостью.\n\n"
        "Правила ответов:\n"
        "1. Если человек говорит, что ему плохо, тяжело, тревожно или одиноко, прояви искреннее сочувствие и понимание "
        "(в стиле старшего товарища по программе), напомни, что он не одинок, и предложи опцию обратиться к живому служащему.\n"
        "2. Отвечай на вопросы о программе АА, шагах, традициях и сленге, опираясь на литературу АА ('Большая Книга', '12 Шагов и 12 Традиций', 'Жить Трезвым').\n"
        "3. Если вопрос вообще не относится к алкоголизму, выздоровлению или состоянию человека, мягко и тепло верни разговор к теме программы.\n"
        "4. Пиши просто, тепло, без морализаторства и канцелярита."
    )

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Groq API Error [{response.status}]: {error_text}")
                    return "Извините, произошла ошибка при обращении к помощнику. Пожалуйста, попробуйте позже."
                
                data = await response.json()
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Exception during Groq request: {e}")
        return "Извините, произошла ошибка при обращении к помощнику. Пожалуйста, попробуйте позже или нажмите кнопку вызова служащего."