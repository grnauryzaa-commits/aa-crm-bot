import psycopg2
from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from config import ADMINS, DATABASE_URL
from database import get_user_language

router = Router()


class EditSponsorState(StatesGroup):
  waiting_for_new_value = State()


class SponsorForm(StatesGroup):
  waiting_for_name = State()


# Словари локализации для спонсоров
SPONSOR_TEXTS = {
    "ru": {
        "reg_title": (
            "📝 <b>Регистрация анкеты спонсора</b>\n\nПожалуйста, введите ваше"
            " имя (или как к вам обращаться в сообществе):"
        ),
        "choose_list": "👥 Выберите список:",
        "empty_list": "Список {label} пока пуст.",
        "not_found": "⚠️ Спонсор не найден в базе данных.",
        "access_denied": "⚠️ Вы можете редактировать только свою анкету!",
        "success_update": "✅ Данные успешно обновлены!",
        "error_update": "❌ Произошла ошибка при сохранении.",
        "edit_prompt": "⚙️ Выберите, какое поле вы хотите изменить:",
        "btn_brothers": "👦 Братья",
        "btn_sisters": "👧 Сестры",
        "btn_back": "⬅️ Назад",
        "btn_forward": "Вперед ➡️",
        "btn_edit": "✏️ Редактировать анкету",
        "fields": {
            "age": "новый возраст (цифрой от 18 до 100)",
            "sobriety": "новый срок трезвости",
            "city": "новый город",
            "phone": "новый номер телефона",
            "program_info": "новую информацию об опыте",
        },
    },
    "kk": {
        "reg_title": (
            "📝 <b>Демеуші сауалнамасын тіркеу</b>\n\nАтыңызды (немесе"
            " қауымдастықта қалай атау керек екенін) енгізіңіз:"
        ),
        "choose_list": "👥 Тізімді таңдаңыз:",
        "empty_list": "{label} тізімі әзірге бос.",
        "not_found": "⚠️ Демеуші деректер базасынан табылмады.",
        "access_denied": "⚠️ Сіз тек өз сауалнамаңызды өңдей аласыз!",
        "success_update": "✅ Деректер сәтті жаңартылды!",
        "error_update": "❌ Сақтау кезінде қате орын алды.",
        "edit_prompt": "⚙️ Өзгерткіңіз келетін өрісті таңдаңыз:",
        "btn_brothers": "👦 Бауырлар",
        "btn_sisters": "👧 Әпкелер",
        "btn_back": "⬅️ Артқа",
        "btn_forward": "Алға ➡️",
        "btn_edit": "✏️ Сауалнаманы өңдеу",
        "fields": {
            "age": "жаңа жас (18 бен 100 аралығындағы сан)",
            "sobriety": "жаңа сабыр/тазалық мерзімі",
            "city": "жаңа қала",
            "phone": "жаңа телефон нөмірі",
            "program_info": "тәжірибе туралы жаңа ақпарат",
        },
    },
}


@router.callback_query(F.data == "start_sponsor_registration")
async def start_sponsor_registration_handler(
    callback: CallbackQuery, state: FSMContext
):
  lang = await get_user_language(callback.from_user.id)
  t = SPONSOR_TEXTS.get(lang, SPONSOR_TEXTS["ru"])

  await callback.message.delete()
  await callback.message.answer(t["reg_title"], parse_mode="HTML")
  await state.set_state(SponsorForm.waiting_for_name)
  await callback.answer()


@router.message(F.text.in_({"🤝 Спонсоры", "🤝 Демеушілер"}))
@router.callback_query(F.data == "menu_sponsors")
async def sponsors_menu(event: Message | CallbackQuery):
  lang = await get_user_language(event.from_user.id)
  t = SPONSOR_TEXTS.get(lang, SPONSOR_TEXTS["ru"])

  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text=t["btn_brothers"], callback_data="list_brothers_0"
              )
          ],
          [
              InlineKeyboardButton(
                  text=t["btn_sisters"], callback_data="list_sisters_0"
              )
          ],
      ]
  )
  if isinstance(event, Message):
    await event.answer(t["choose_list"], reply_markup=keyboard)
  else:
    await event.message.edit_text(t["choose_list"], reply_markup=keyboard)
    await event.answer()


@router.callback_query(F.data.startswith(("list_brothers_", "list_sisters_")))
async def show_list_page(callback: CallbackQuery):
  lang = await get_user_language(callback.from_user.id)
  t = SPONSOR_TEXTS.get(lang, SPONSOR_TEXTS["ru"])

  parts = callback.data.split("_")
  list_type = parts[1]
  page = int(parts[2])

  gender_filter = (
      "OR gender ILIKE '%муж%'"
      if list_type == "brothers"
      else "OR gender ILIKE '%жен%'"
  )
  label = (
      (
          "Братья"
          if lang == "ru"
          else "Бауырлар"
      )
      if list_type == "brothers"
      else ("Сестры" if lang == "ru" else "Әпкелер")
  )
  db_keyword = "брат" if list_type == "brothers" else "сестр"

  conn = psycopg2.connect(DATABASE_URL)
  cur = conn.cursor()
  cur.execute(
      f"SELECT user_id, name, age, city, sobriety FROM sponsors WHERE gender"
      f" ILIKE '%{db_keyword}%' {gender_filter};"
  )
  all_sponsors = cur.fetchall()
  cur.close()
  conn.close()

  if not all_sponsors:
    await callback.answer(
        t["empty_list"].format(label=label), show_alert=True
    )
    return

  PER_PAGE = 5
  total_pages = (len(all_sponsors) + PER_PAGE - 1) // PER_PAGE
  start_idx = page * PER_PAGE
  end_idx = start_idx + PER_PAGE
  current_sponsors = all_sponsors[start_idx:end_idx]

  keyboard = []
  for uid, name, age, city, sobriety in current_sponsors:
    button_text = f"{name}, {age} | {city or 'Город'} | {sobriety}"
    keyboard.append([
        InlineKeyboardButton(
            text=button_text,
            callback_data=f"view_sp_{uid}_{list_type}_{page}",
        )
    ])

  nav_buttons = []
  if page > 0:
    nav_buttons.append(
        InlineKeyboardButton(
            text=t["btn_back"], callback_data=f"list_{list_type}_{page - 1}"
        )
    )
  if end_idx < len(all_sponsors):
    nav_buttons.append(
        InlineKeyboardButton(
            text=t["btn_forward"], callback_data=f"list_{list_type}_{page + 1}"
        )
    )

  if nav_buttons:
    keyboard.append(nav_buttons)

  keyboard.append(
      [InlineKeyboardButton(text=t["btn_back"], callback_data="menu_sponsors")]
  )

  await callback.message.edit_text(
      f"📖 ({label}) — {page + 1} / {total_pages}:",
      reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
  )


@router.callback_query(F.data.startswith("view_sp_"))
async def show_details(callback: CallbackQuery):
  lang = await get_user_language(callback.from_user.id)
  t = SPONSOR_TEXTS.get(lang, SPONSOR_TEXTS["ru"])

  parts = callback.data.split("_")
  user_id = parts[2]
  list_type = parts[3]
  page = parts[4]

  conn = psycopg2.connect(DATABASE_URL)
  cur = conn.cursor()
  cur.execute(
      "SELECT name, gender, age, sobriety, city, username, phone, program_info"
      " FROM sponsors WHERE user_id = %s;",
      (user_id,),
  )
  sp = cur.fetchone()
  cur.close()
  conn.close()

  if sp:
    name, gender, age, sobriety, city, username, phone, program_info = sp
    tg_contact = f"@{username}" if username and username not in ("-", "нет") else f"ID: {user_id}"

    text = (
        f"👤 Спонсор: {name} ({gender}), {age}\n🕊 Трезвость: {sobriety}\n📍"
        f" Город: {city}\n📖 Опыт: {program_info}\n✈️ Telegram:"
        f" {tg_contact}\n📞 Телефон: {phone}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                text=t["btn_back"], callback_data=f"list_{list_type}_{page}"
            )
        ]
    ]

    current_user_id = callback.from_user.id
    if current_user_id == int(user_id) or current_user_id in ADMINS:
      keyboard.insert(
          0,
          [
              InlineKeyboardButton(
                  text=t["btn_edit"],
                  callback_data=f"edit_menu_{user_id}_{list_type}_{page}",
              )
          ],
      )

    await callback.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
  else:
    await callback.answer(t["not_found"], show_alert=True)


@router.callback_query(F.data.startswith("edit_menu_"))
async def edit_menu(callback: CallbackQuery):
  lang = await get_user_language(callback.from_user.id)
  t = SPONSOR_TEXTS.get(lang, SPONSOR_TEXTS["ru"])

  parts = callback.data.split("_")
  user_id = parts[2]
  list_type = parts[3]
  page = parts[4]

  if callback.from_user.id != int(user_id) and callback.from_user.id not in ADMINS:
    await callback.answer(t["access_denied"], show_alert=True)
    return

  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="📅 Возраст",
                  callback_data=f"edit_field_{user_id}_age_{list_type}_{page}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🕊 Срок трезвости",
                  callback_data=(
                      f"edit_field_{user_id}_sobriety_{list_type}_{page}"
                  ),
              )
          ],
          [
              InlineKeyboardButton(
                  text="📍 Город",
                  callback_data=f"edit_field_{user_id}_city_{list_type}_{page}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📞 Телефон",
                  callback_data=f"edit_field_{user_id}_phone_{list_type}_{page}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📖 Опыт",
                  callback_data=(
                      f"edit_field_{user_id}_programinfo_{list_type}_{page}"
                  ),
              )
          ],
          [
              InlineKeyboardButton(
                  text=t["btn_back"],
                  callback_data=f"view_sp_{user_id}_{list_type}_{page}",
              )
          ],
      ]
  )
  await callback.message.edit_text(t["edit_prompt"], reply_markup=keyboard)


@router.callback_query(F.data.startswith("edit_field_"))
async def start_editing_field(callback: CallbackQuery, state: FSMContext):
  lang = await get_user_language(callback.from_user.id)
  t = SPONSOR_TEXTS.get(lang, SPONSOR_TEXTS["ru"])

  parts = callback.data.split("_")
  user_id = parts[2]
  field_name = parts[3]
  list_type = parts[4]
  page = parts[5]

  if field_name == "programinfo":
    field_name = "program_info"

  if callback.from_user.id != int(user_id) and callback.from_user.id not in ADMINS:
    await callback.answer("⚠️ Доступ запрещен!", show_alert=True)
    return

  await state.update_data(
      target_user_id=user_id,
      field_name=field_name,
      list_type=list_type,
      page=page,
  )
  await state.set_state(EditSponsorState.waiting_for_new_value)

  field_desc = t["fields"].get(field_name, "значение")
  await callback.message.answer(f"✍️ Напишите {field_desc}:")
  await callback.answer()


@router.message(EditSponsorState.waiting_for_new_value)
async def save_edited_field(message: Message, state: FSMContext):
  new_value = message.text.strip()
  data = await state.get_data()
  target_user_id = data.get("target_user_id")
  field_name = data.get("field_name")

  allowed_fields = ["age", "sobriety", "city", "phone", "program_info"]
  if field_name not in allowed_fields:
    await message.answer("Ошибка поля.")
    await state.clear()
    return

  if field_name == "age":
    if not new_value.isdigit() or not (18 <= int(new_value) <= 100):
      await message.answer(
          "⚠️ Возраст должен состоять только из цифр (от 18 до 100)."
          " Попробуйте еще раз:"
      )
      return

  try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    query = f"UPDATE sponsors SET {field_name} = %s WHERE user_id = %s;"
    cur.execute(query, (new_value, target_user_id))
    conn.commit()
    cur.close()
    conn.close()

    await message.answer("✅ Данные успешно обновлены!")
    await state.clear()
  except Exception as e:
    print(f"Ошибка при обновлении: {e}")
    await message.answer("❌ Произошла ошибка при сохранении.")
    await state.clear()