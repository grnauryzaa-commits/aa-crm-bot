import os
from openai import AsyncOpenAI
import logging

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

AA_SYSTEM_PROMPT = """Ты — заботливый, мудрый и эмпатичный цифровой помощник для новичков в сообществе Анонимных Алкоголиков (АА). Твоя задача — поддерживать новичков, отвечать на их вопросы о программе, Шагах, традициях и жизни в трезвости, опираясь исключительно на принципы и литературу АА."""

async def ask_ai_for_beginner(user_message: str) -> str:
    try:
        sys_msg = {"role": "system", "content": AA_SYSTEM_PROMPT}
        usr_msg = {"role": "user", "content": user_message}
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[sys_msg, usr_msg],
            max_tokens=600,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Ошибка при запросе к AI: {e}")
        return "Извините, сейчас у меня не получается ответить. Воспользуйтесь кнопками меню ниже."