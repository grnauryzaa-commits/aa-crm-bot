import asyncio
import logging
from aiogram import F, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import DATABASE_URL as DB_URL
import psycopg2

router = Router()


def _get_sponsors_by_gender(gender: str):
  conn = psycopg2.connect(DB_URL)
  cur = conn.cursor()
  cur.execute(
      "SELECT name, age, sobriety, city, program_info, username, phone FROM"
      " sponsors WHERE gender = %s;",
      (gender,),
  )
  rows = cur.fetchall()
  cur.close()
  conn.close()
  return rows


@router.message(F.text == "🤝 Спонсоры")
async def choose_gender(message: types.Message):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🙋‍♂️ Братья", callback_data="view_sponsors:Братья:0"
          ),
          InlineKeyboardButton(
              text="🙋‍♀️ Сестры", callback_data="view_sponsors:Сестры:0"
          ),
      ]]
  )
  await message.answer("👥 Выберите список:", reply_markup=kb)


@router.callback_query(F.data.startswith("view_sponsors:"))
async def view_sponsors_page(callback: types.CallbackQuery):
  _, gender, offset_str = callback.data.split(":")
  offset = int(offset_str)
  sponsors = await asyncio.to_thread(_get_sponsors_by_gender, gender)

  if not sponsors:
    await callback.answer(f"Список {gender} пока пуст.", show_alert=True)
    return

  LIMIT = 3
  chunk = sponsors[offset : offset + LIMIT]
  total = len(sponsors)

  if not chunk:
    await callback.answer("Больше анкет нет.", show_alert=True)
    return

  try:
    await callback.message.delete()
  except:
    pass

  await callback.message.answer(
      f"🔎 Список: <b>{gender}</b>. Страница {int(offset/LIMIT)+1}:",
      parse_mode="HTML",
  )

  for row in chunk:
    name, age, sobriety, city, program_info, username, phone = row

    # Красиво форматируем юзернейм
    tg_link = f"@{username.lstrip('@')}" if username else "Не указан"

    # Современная карточка с HTML-разметкой
    text = (
        f"<b>👤 {name}</b>, <i>{age} лет</i>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🕊 <b>Срок трезвости:</b> {sobriety}\n"
        f"📍 <b>Город:</b> {city}\n"
        f"📖 <b>О программе:</b> {program_info}\n"
        f"✈️ <b>Telegram:</b> {tg_link}\n"
        f"📞 <b>Телефон:</b> {phone or 'Не указан'}"
    )

    await callback.message.answer(text, parse_mode="HTML")

  btns = []
  if offset + LIMIT < total:
    btns.append(
        InlineKeyboardButton(
            text="➡️ Еще",
            callback_data=f"view_sponsors:{gender}:{offset + LIMIT}",
        )
    )
  btns.append(
      InlineKeyboardButton(
          text="🔄 Смена пола", callback_data="back_to_gender"
      )
  )

  await callback.message.answer(
      f"Всего анкет: {total}",
      reply_markup=InlineKeyboardMarkup(inline_keyboard=[btns]),
  )
  await callback.answer()


@router.callback_query(F.data == "back_to_gender")
async def back_gender(callback: types.CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🙋‍♂️ Братья", callback_data="view_sponsors:Братья:0"
          ),
          InlineKeyboardButton(
              text="🙋‍♀️ Сестры", callback_data="view_sponsors:Сестры:0"
          ),
      ]]
  )
  try:
    await callback.message.edit_text("👥 Выберите список:", reply_markup=kb)
  except:
    await callback.message.answer("👥 Выберите список:", reply_markup=kb)
  await callback.answer()