# routers/ai_helper.py
import aiohttp
import logging
from config import GROQ_API_KEY
from database import add_message_to_history, get_recent_history, get_user_language
from knowledge_base import find_canonical_context
from rag_search import find_relevant_context


async def ask_ai_for_beginner(user_id: int, user_message: str) -> str:
  # 1. Точный запрос про шаг/традицию/концепцию — отдаём цитату без ИИ
  canonical = find_canonical_context(user_message)
  if canonical:
    return canonical

  # 2. Иначе ищем релевантные фрагменты в базе (RAG)
  context = find_relevant_context(user_message)

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

  # Формируем блок справочного материала
  if context:
    context_block = (
        "СПРАВОЧНЫЙ МАТЕРИАЛ ИЗ ОФИЦИАЛЬНЫХ ТЕКСТОВ АА:\n"
        f"{context}\n"
    )
  else:
    context_block = ""

  system_prompt = (
      "Ты — тёплый, живой помощник Telegram-бота сообщества Анонимных "
      "Алкоголиков (АА) в Казахстане. К тебе обращаются люди в трудные "
      "моменты: кто-то борется с зависимостью, кто-то переживает за близкого, "
      "кто-то только делает первые шаги.\n\n"
      "Твоя задача — отвечать по-человечески, с теплом и без осуждения. "
      "Ты не читаешь лекции, не морализируешь, не даёшь медицинских советов. "
      "Ты поддерживаешь, объясняешь принципы программы АА и направляешь "
      "к живой помощи, когда это уместно.\n\n"
      f"{context_block}\n"
      f"{lang_instruction}\n\n"
      "КАК ОТВЕЧАТЬ:\n"
      "1. Начни с сочувствия или признания чувств человека — "
      "«Я слышу тебя», «Это правда тяжело», «Спасибо, что поделился».\n"
      "2. Отвечай тепло и по-дружески, 4–7 предложений. Без списков и "
      "канцелярита.\n"
      "3. Используй СПРАВОЧНЫЙ МАТЕРИАЛ выше как источник истины. "
      "Не выдумывай факты, цитаты, шаги, которых там нет.\n"
      "4. Если в справочном материале нет ответа — мягко скажи: "
      "«Лучше уточнить у живого служащего» и напомни про кнопку "
      f"{button_name}.\n"
      "5. Если человек в остром состоянии (срыв, паника, отчаяние, "
      "суицидальные мысли) — предложи связаться с живым служащим через "
      f"кнопку {button_name} или позвонить на телефон доверия.\n"
      "6. Не ставь диагнозы, не давай медицинских советов, не обещай "
      "выздоровления.\n"
      "7. Не представляйся членом АА и не говори от первого лица как "
      "алкоголик. Ты — помощник сообщества.\n"
      "8. Всегда завершай ответ законченной мыслью, не обрывай на полуслове."
  )

  messages = [{"role": "system", "content": system_prompt}] + history

  payload = {
      "model": "openai/gpt-oss-20b",
      "messages": messages,
      "temperature": 0.6,
      "max_tokens": 700,
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