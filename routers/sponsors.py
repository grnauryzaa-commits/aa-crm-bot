import psycopg2, logging, asyncio
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import DATABASE_URL as DB_URL

router = Router()

def _get_sponsors_by_gender(gender: str):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT name, age, sobriety, city, program_info, username, phone FROM sponsors WHERE gender = %s;", (gender,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@router.message(F.text == "🤝 Спонсоры")
async def choose_gender(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🙋‍♂️ Братья", callback_data="view_sponsors:Братья:0"),
        InlineKeyboardButton(text="🙋‍♀️ Сестры", callback_data="view_sponsors:Сестры:0")
    ]])
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

    try: await callback.message.delete()
    except: pass

    await callback.message.answer(f"🔎 Список: {gender}. Страница {int(offset/LIMIT)+1}:")
    for row in chunk:
        text = f"👤 {row[0]}, {row[1]} лет\n🕊 {row[2]}\n📍 {row[3]}\n📖 {row[4]}\n✈️ {row[5]}\n📞 {row[6]}\n━━━━━━━━━"
        await callback.message.answer(text)

    btns = []
    if offset + LIMIT < total:
        btns.append(InlineKeyboardButton(text="➡️ Еще", callback_data=f"view_sponsors:{gender}:{offset + LIMIT}"))
    btns.append(InlineKeyboardButton(text="🔄 Смена пола", callback_data="back_to_gender"))
    
    await callback.message.answer(f"Всего: {total}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[btns]))
    await callback.answer()

@router.callback_query(F.data == "back_to_gender")
async def back_gender(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🙋‍♂️ Братья", callback_data="view_sponsors:Братья:0"),
        InlineKeyboardButton(text="🙋‍♀️ Сестры", callback_data="view_sponsors:Сестры:0")
    ]])
    await callback.message.edit_text("👥 Выберите список:", reply_markup=kb)