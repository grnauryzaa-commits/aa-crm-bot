import aiohttp
import logging
from config import GROQ_API_KEY
from database import add_message_to_history, get_recent_history, get_user_language
from knowledge_base import find_canonical_context


async def ask_ai_for_beginner(user_id: int, user_message: str) -> str:
  # 1. Сначала проверяем каноническую базу — если вопрос про шаг/традицию/концепцию,
  #    отдаём точный текст БЕЗ обращения к ИИ
  canonical = find_canonical_context(user_message)
  if canonical:
    await add_message_to_history(user_id, "user", user_message)
    await add_message_to_history(user_id, "assistant", canonical)
    return canonical

  # 2. Если канонического текста нет — идём в Groq
  if not GROQ_API_KEY:
    return (
        "Алкоголь умеет нас изолировать, но сейчас ты можешь сделать вдох и"
        " обратиться к живому другу по программе."
    )

  await add_message_to_history(user_id, "user", user_message)

  lang = await get_user_language(user_id)
  lang_instruction = (
      "Отвечай строго на казахском языке. (Қазақ тілінде жауап бер.)"
      if lang == "kk"
      else "Отвечай строго на русском языке."
  )

  button_name = (
      "«👤 Тірі қызметкерді шақыру»"
      if lang == "kk"
      else "«👤 Позвать живого служащего»"
  )

  history = await get_recent_history(user_id, limit=6)

  url = "https://api.groq.com/openai/v1/chat/completions"
  headers = {
      "Authorization": f"Bearer {GROQ_API_KEY}",
      "Content-Type": "application/json",
  }

  system_prompt = (
      "Ты — информационный помощник Telegram-бота сообщества "
      "Анонимных Алкоголиков (АА) в Казахстане.\n"
      "Ты НЕ человек и НЕ участник программы. Ты не говоришь от первого лица "
      "как член АА и не представляешься алкоголиком или служащим.\n"
      "Твоя задача — коротко и по делу отвечать на вопросы о программе АА, "
      "12 шагах, 12 традициях, группах и сайте aaorg.kz.\n\n"
      f"{lang_instruction}\n\n"
      "ПРАВИЛА:\n"
      "1. Отвечай тепло и дружелюбно, но не более 4–5 предложений.\n"
      "2. Никогда не начинай ответ со слов «Я — член АА», «Я — алкоголик», "
      "«Я — служащий» и подобных. Ты программа, а не человек.\n"
      "3. Если пользователь спрашивает «кто ты» — отвечай: "
      "«Я информационный помощник сообщества АА в Казахстане».\n"
      "4. Ссылайся только на Большую Книгу АА, книгу «Двенадцать Шагов и "
      "Двенадцать Традиций» и сайт aaorg.kz.\n"
      f"5. Всегда напоминай про кнопку {button_name} для связи с живым "
      "служащим, если вопрос касается личной поддержки.\n"
      "6. Отвечай законченными предложениями, не обрывай мысль."
  )

  messages = [{"role": "system", "content": system_prompt}] + history

  payload = {
      "model": "openai/gpt-oss-20b",
      "messages": messages,
      "temperature": 0.4,
      "max_tokens": 500,
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
        else:
          error_text = await response.text()
          logging.error(f"Groq API error {response.status}: {error_text}")
        return (
            "Я внимательно тебя слушал, но на секунду отвлекся. Если вопрос"
            " срочный, нажми кнопку связи с дежурным ниже."
        )
  except Exception as e:
    logging.error(f"Exception during AI request: {e}")
    return (
        "Произошел небольшой технический сбой. Главное — оставайся трезвым,"
        " посмотри расписание групп на aaorg.kz."
    )