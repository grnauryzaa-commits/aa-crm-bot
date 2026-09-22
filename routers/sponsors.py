import html
import traceback
import psycopg2
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from config import ADMINS, DATABASE_URL
from database import get_user_language, save_sponsor_draft
from routers.states import SponsorForm

router = Router()


class EditSponsorState(StatesGroup):
  waiting_for_new_value = State()


FORM_TEXTS = {
    "ru": {
        "btn_become": "➕ Стать спонсором",
        "menu_title": (
            "➕ <b>Стать спонсором в АА</b>\n\nСпонсор — это человек, который"
            " прошел Шаги и готов делиться опытом с другими."
        ),
        "btn_fill": "📝 Заполнить анкету спонсора",
        "ask_name": "👤 Напиши свое имя:",
        "ask_gender": "Какой твой пол? (Брат / Сестра)",
        "ask_age": "📅 Напиши свой возраст (цифрой):",
        "ask_sobriety": "🕊 Какой у тебя срок трезвости?",
        "ask_city": "📍 Из какого ты города?",
        "ask_program": "📖 Напиши коротко о своем опыте:",
        "ask_phone": "📞 Напиши свой номер телефона для связи:",
        "success_draft": (
            "✅ Твоя анкета успешно отправлена на модерацию администратору!"
        ),
        "admin_title": "🔔 ЗАЯВКА НА РЕГИСТРАЦИЮ СПОНСОРА",
        "admin_approve": "✅ Одобрить карточку",
        "admin_decline": "❌ Отклонить",
        "approved_alert": "Анкета одобрена!",
        "declined_alert": "Анкета отклонена.",
        "user_approved": "🎉 Поздравляем! Ваша анкета спонсора одобрена.",
        "user_declined": "❌ К сожалению, ваша анкета отклонена.",
        "fallback_become": "➕ Стать спонсором",
        "fallback_list": "📋 Список спонсоров",
        "fallback_main": "🏠 Главное меню",
        "choose_list": "👥 Выберите список:",
        "empty_list": "Список {label} пока пуст.",
        "not_found": "⚠️ Спонсор не найден в базе данных.",
        "btn_brothers": "👦 Братья",
        "btn_sisters": "👧 Сестры",
        "btn_back": "⬅️ Назад",
        "btn_forward": "Вперед ➡️",
        "btn_edit": "✏️ Редактировать анкету",
        "label_brothers": "Братья",
        "label_sisters": "Сестры",
        "default_city": "Город не указан",
    },
    "kk": {
        "btn_become": "➕ Демеуші болу",
        "menu_title": (
            "➕ <b>АА-да демеуші болу</b>\n\nДемеуші — тәжірибе бөлісуге дайын"
            " адам."
        ),
        "btn_fill": "📝 Демеуші сауалнамасын толтыру",
        "ask_name": "👤 Атыңызды жазыңыз:",
        "ask_gender": "Жынысыңыз қандай? (Бауыр / Әпке)",
        "ask_age": "📅 Жасыңызды жазыңыз (санмен):",
        "ask_sobriety": "🕊 Тазалық мерзіміңіз қандай?",
        "ask_city": "📍 Қай қаладансыз?",
        "ask_program": "📖 Тәжірибеңіз туралы қысқаша жазыңыз:",
        "ask_phone": "📞 Телефон нөміріңізді жазыңыз:",
        "success_draft": "✅ Сауалнамаңыз әкімшіге жіберілді!",
        "admin_title": "🔔 ДЕМЕУШІНІ ТІРКЕУ ӨТІНІШІ",
        "admin_approve": "✅ Мақұлдау",
        "admin_decline": "❌ Бас тарту",
        "approved_alert": "Мақұлданды!",
        "declined_alert": "Қабылданбады.",
        "user_approved": "🎉 Құттықтаймыз! Сауалнамаңыз мақұлданды.",
        "user_declined": "❌ Өкінішке орай, сауалнамаңыз қабылданбады.",
        "fallback_become": "➕ Демеуші болу",
        "fallback_list": "📋 Тізім",
        "fallback_main": "🏠 Басты мәзір",
        "choose_list": "👥 Тізімді таңдаңыз:",
        "empty_list": "{label} тізімі бос.",
        "not_found": "⚠️ Деректер базасынан табылмады.",
        "btn_brothers": "👦 Бауырлар",
        "btn_sisters": "👧 Әпкелер",
        "btn_back": "⬅️ Артқа",
        "btn_forward": "Алға ➡️",
        "btn_edit": "✏️ Өңдеу",
        "label_brothers": "Бауырлар",
        "label_sisters": "Әпкелер",
        "default_city": "Қала көрсетілмеген",
    },
}


def get_fallback_menu_keyboard(lang: str = "ru"):
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
  return ReplyKeyboardMarkup(
      keyboard=[
          [
              KeyboardButton(text=t["fallback_become"]),
              KeyboardButton(text=t["fallback_list"]),
          ],
          [KeyboardButton(text=t["fallback_main"])],
      ],
      resize_keyboard=True,
  )


@router.message(
    F.chat.type == "private",
    (
        F.text.in_({"➕ Стать спонсором", "➕ Демеуші болу"})
        | F.text.contains("Демеуші")
        | F.text.contains("Спонсор")
    ),
)
async def start_form_text(message: Message, state: FSMContext):
  try:
    lang = (await get_user_language(message.from_user.id)) or "ru"
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t["btn_fill"],
                    callback_data=f"start_sponsor_registration_{lang}",
                )
            ]
        ]
    )
    await message.answer(
        t["menu_title"], reply_markup=keyboard, parse_mode="HTML"
    )
  except Exception as e:
    print(f"Error in start_form_text: {e}")


@router.message(
    F.chat.type == "private",
    (
        F.text.in_({"🤝 Спонсоры", "🤝 Демеушілер"})
        | F.text.contains("Демеушілер")
        | F.text.contains("Спонсоры")
    ),
)
@router.callback_query(
    (F.data == "menu_sponsors") | (F.data.startswith("menu_sponsors_"))
)
async def sponsors_menu(event: Message | CallbackQuery):
  user_id = event.from_user.id

  if isinstance(event, Message):
    if "Демеушілер" in event.text:
      lang = "kk"
    else:
      lang = (await get_user_language(user_id)) or "ru"
  else:
    parts = event.data.split("_")
    if len(parts) >= 3 and parts[-1] in ["ru", "kk"]:
      lang = parts[-1]
    else:
      lang = (await get_user_language(user_id)) or "ru"

  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text=t["btn_brothers"],
                  callback_data=f"list_brothers_0_{lang}",
              )
          ],
          [
              InlineKeyboardButton(
                  text=t["btn_sisters"], callback_data=f"list_sisters_0_{lang}"
              )
          ],
      ]
  )
  if isinstance(event, Message):
    await event.answer(t["choose_list"], reply_markup=keyboard)
  else:
    try:
      await event.message.edit_text(t["choose_list"], reply_markup=keyboard)
    except Exception:
      await event.message.answer(t["choose_list"], reply_markup=keyboard)
    await event.answer()


@router.callback_query(
    F.data.startswith(("list_brothers_", "list_sisters_", "list_"))
)
async def show_list_page(callback: CallbackQuery):
  parts = callback.data.split("_")
  try:
    if len(parts) >= 4 and parts[1] in ["brothers", "sisters"]:
      list_type = parts[1]
      page = int(parts[2])
      lang = parts[3] if parts[3] in ["ru", "kk"] else "ru"
    elif len(parts) >= 3 and parts[0] == "list":
      list_type = parts[1]
      page = int(parts[2])
      lang = parts[3] if len(parts) > 3 and parts[3] in ["ru", "kk"] else "ru"
    else:
      list_type = "brothers" if "brothers" in callback.data else "sisters"
      page = 0
      lang = "ru"
  except (ValueError, IndexError):
    page = 0
    list_type = "brothers"
    lang = "ru"

  if not lang or lang not in ["ru", "kk"]:
    lang = (await get_user_language(callback.from_user.id)) or "ru"

  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
  label = t["label_brothers"] if list_type == "brothers" else t["label_sisters"]

  if list_type == "brothers":
    db_query_filter = (
        "gender ILIKE '%брат%' OR gender ILIKE '%муж%' OR gender ILIKE"
        " '%бауыр%'"
    )
  else:
    db_query_filter = (
        "gender ILIKE '%сестр%' OR gender ILIKE '%жен%' OR gender ILIKE"
        " '%әпке%'"
    )

  try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        f"SELECT user_id, name, age, city, sobriety FROM sponsors WHERE"
        f" {db_query_filter};"
    )
    all_sponsors = cur.fetchall()
    cur.close()
    conn.close()
  except Exception as e:
    print(f"DB Error: {e}")
    all_sponsors = []

  if not all_sponsors:
    await callback.answer(
        t["empty_list"].format(label=label), show_alert=True
    )
    return

  PER_PAGE = 5
  total_pages = (len(all_sponsors) + PER_PAGE - 1) // PER_PAGE
  if page >= total_pages:
    page = total_pages - 1
  if page < 0:
    page = 0

  start_idx = page * PER_PAGE
  end_idx = start_idx + PER_PAGE
  current_sponsors = all_sponsors[start_idx:end_idx]

  keyboard = []
  for uid, name, age, city, sobriety in current_sponsors:
    city_name = city if city else t["default_city"]
    keyboard.append([
        InlineKeyboardButton(
            text=f"{name}, {age} | {city_name} | {sobriety}",
            callback_data=f"view_sp_{uid}_{list_type}_{page}_{lang}",
        )
    ])

  nav_buttons = []
  if page > 0:
    nav_buttons.append(
        InlineKeyboardButton(
            text=t["btn_back"],
            callback_data=f"list_{list_type}_{page - 1}_{lang}",
        )
    )
  if end_idx < len(all_sponsors):
    nav_buttons.append(
        InlineKeyboardButton(
            text=t["btn_forward"],
            callback_data=f"list_{list_type}_{page + 1}_{lang}",
        )
    )

  if nav_buttons:
    keyboard.append(nav_buttons)
  keyboard.append([
      InlineKeyboardButton(
          text=t["btn_back"], callback_data=f"menu_sponsors_{lang}"
      )
  ])

  try:
    await callback.message.edit_text(
        f"📖 ({label}) — {page + 1} / {total_pages}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )
  except Exception:
    pass
  await callback.answer()


@router.callback_query(F.data.startswith("view_sp_"))
async def show_details(callback: CallbackQuery):
  parts = callback.data.split("_")
  if len(parts) < 6:
    await callback.answer("Ошибка", show_alert=True)
    return

  user_id, list_type, page, lang = parts[2], parts[3], parts[4], parts[5]
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  try:
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
  except Exception as e:
    print(f"DB Error: {e}")
    sp = None

  if sp:
    name, gender, age, sobriety, city, username, phone, program_info = sp
    tg_contact = (
        f"@{username}"
        if username and username not in ("-", "нет")
        else f"ID: {user_id}"
    )

    text = (
        f"👤 Спонсор: {name} ({gender}), {age}\n🕊 Трезвость:"
        f" {sobriety}\n📍 Город: {city}\n📖 Опыт: {program_info}\n✈️ Telegram:"
        f" {tg_contact}\n📞 Телефон: {phone}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                text=t["btn_back"],
                callback_data=f"list_{list_type}_{page}_{lang}",
            )
        ]
    ]

    if callback.from_user.id == int(user_id) or callback.from_user.id in ADMINS:
      keyboard.insert(
          0,
          [
              InlineKeyboardButton(
                  text=t["btn_edit"],
                  callback_data=(
                      f"edit_menu_{user_id}_{list_type}_{page}_{lang}"
                  ),
              )
          ],
      )

    try:
      await callback.message.edit_text(
          text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
      )
    except Exception:
      pass
  else:
    await callback.answer(t["not_found"], show_alert=True)
  await callback.answer()


@router.callback_query(F.data.startswith("edit_menu_"))
async def edit_menu(callback: CallbackQuery):
  parts = callback.data.split("_")
  if len(parts) < 6:
    return
  user_id, list_type, page, lang = parts[2], parts[3], parts[4], parts[5]

  if callback.from_user.id != int(user_id) and callback.from_user.id not in ADMINS:
    await callback.answer(
        "⚠️ Вы можете редактировать только свою анкету!", show_alert=True
    )
    return

  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="📅 Возраст",
                  callback_data=(
                      f"edit_field_{user_id}_age_{list_type}_{page}_{lang}"
                  ),
              )
          ],
          [
              InlineKeyboardButton(
                  text="🕊 Срок трезвости",
                  callback_data=(
                      f"edit_field_{user_id}_sobriety_{list_type}_{page}_{lang}"
                  ),
              )
          ],
          [
              InlineKeyboardButton(
                  text="📍 Город",
                  callback_data=(
                      f"edit_field_{user_id}_city_{list_type}_{page}_{lang}"
                  ),
              )
          ],
          [
              InlineKeyboardButton(
                  text="📞 Телефон",
                  callback_data=(
                      f"edit_field_{user_id}_phone_{list_type}_{page}_{lang}"
                  ),
              )
          ],
          [
              InlineKeyboardButton(
                  text="📖 Опыт / Программа",
                  callback_data=(
                      f"edit_field_{user_id}_programinfo_{list_type}_{page}_{lang}"
                  ),
              )
          ],
          [
              InlineKeyboardButton(
                  text="⬅️ Назад",
                  callback_data=f"view_sp_{user_id}_{list_type}_{page}_{lang}",
              )
          ],
      ]
  )
  try:
    await callback.message.edit_text(
        "⚙️ Выберите, какое поле вы хотите изменить:", reply_markup=keyboard
    )
  except Exception:
    pass
  await callback.answer()


@router.callback_query(F.data.startswith("edit_field_"))
async def start_editing_field(callback: CallbackQuery, state: FSMContext):
  parts = callback.data.split("_")
  if len(parts) < 7:
    return
  user_id, field_name, list_type, page, lang = (
      parts[2],
      parts[3],
      parts[4],
      parts[5],
      parts[6],
  )
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
      lang=lang,
  )
  await state.set_state(EditSponsorState.waiting_for_new_value)

  await callback.message.answer("✍️ Напишите новое значение в чат:")
  await callback.answer()


@router.message(EditSponsorState.waiting_for_new_value)
async def save_edited_field(message: Message, state: FSMContext):
  new_value = message.text.strip()
  data = await state.get_data()
  target_user_id = data.get("target_user_id")
  field_name = data.get("field_name")
  lang = data.get("lang", "ru")

  if field_name == "age" and (
      not new_value.isdigit() or not (18 <= int(new_value) <= 100)
  ):
    await message.answer("⚠️ Возраст должен быть от 18 до 100. Повторите:")
    return

  try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        f"UPDATE sponsors SET {field_name} = %s WHERE user_id = %s;",
        (new_value, target_user_id),
    )
    conn.commit()
    cur.close()
    conn.close()

    await message.answer(
        "✅ Данные успешно обновлены!",
        reply_markup=get_fallback_menu_keyboard(lang),
    )
    await state.clear()
  except Exception as e:
    print(f"Save error: {e}")
    await message.answer("❌ Ошибка при сохранении.")
    await state.clear()


@router.callback_query(F.data.startswith("start_sponsor_registration"))
async def start_form_callback(callback: CallbackQuery, state: FSMContext):
  if callback.message.chat.type != "private":
    await callback.answer()
    return
  try:
    parts = callback.data.split("_")
    lang = (
        parts[3]
        if len(parts) > 3 and parts[3] in ["ru", "kk"]
        else (await get_user_language(callback.from_user.id) or "ru")
    )
    await state.update_data(lang=lang)
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

    await callback.message.answer(
        t["ask_name"], reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(SponsorForm.name)
    await callback.answer()
  except Exception as e:
    print(f"Error in start_form_callback: {e}")
    traceback.print_exc()


@router.message(F.chat.type == "private", SponsorForm.name)
async def process_name(message: Message, state: FSMContext):
  data = await state.get_data()
  t = FORM_TEXTS.get(data.get("lang", "ru"), FORM_TEXTS["ru"])
  await state.update_data(name=message.text)
  await message.answer(t["ask_gender"])
  await state.set_state(SponsorForm.gender)


@router.message(F.chat.type == "private", SponsorForm.gender)
async def process_gender(message: Message, state: FSMContext):
  data = await state.get_data()
  t = FORM_TEXTS.get(data.get("lang", "ru"), FORM_TEXTS["ru"])
  await state.update_data(gender=message.text)
  await message.answer(t["ask_age"])
  await state.set_state(SponsorForm.age)


@router.message(F.chat.type == "private", SponsorForm.age)
async def process_age(message: Message, state: FSMContext):
  data = await state.get_data()
  t = FORM_TEXTS.get(data.get("lang", "ru"), FORM_TEXTS["ru"])
  await state.update_data(age=message.text)
  await message.answer(t["ask_sobriety"])
  await state.set_state(SponsorForm.sobriety)


@router.message(F.chat.type == "private", SponsorForm.sobriety)
async def process_sobriety(message: Message, state: FSMContext):
  data = await state.get_data()
  t = FORM_TEXTS.get(data.get("lang", "ru"), FORM_TEXTS["ru"])
  await state.update_data(sobriety=message.text)
  await message.answer(t["ask_city"])
  await state.set_state(SponsorForm.city)


@router.message(F.chat.type == "private", SponsorForm.city)
async def process_city(message: Message, state: FSMContext):
  data = await state.get_data()
  t = FORM_TEXTS.get(data.get("lang", "ru"), FORM_TEXTS["ru"])
  await state.update_data(city=message.text)
  await message.answer(t["ask_program"])
  await state.set_state(SponsorForm.program_info)


@router.message(F.chat.type == "private", SponsorForm.program_info)
async def process_program_info(message: Message, state: FSMContext):
  data = await state.get_data()
  t = FORM_TEXTS.get(data.get("lang", "ru"), FORM_TEXTS["ru"])
  await state.update_data(program_info=message.text)
  await message.answer(t["ask_phone"])
  await state.set_state(SponsorForm.phone)


@router.message(F.chat.type == "private", SponsorForm.phone)
async def process_phone(message: Message, state: FSMContext, bot: Bot):
  data = await state.get_data()
  lang = data.get("lang", "ru")
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  await state.update_data(phone=message.text)
  data = await state.get_data()
  tg_id = message.from_user.id

  sponsor_data = {
      "name": data.get("name"),
      "gender": data.get("gender"),
      "age": data.get("age"),
      "sobriety": data.get("sobriety"),
      "city": data.get("city"),
      "program_info": data.get("program_info"),
      "username": message.from_user.username or "нет",
      "phone": data.get("phone"),
  }

  try:
    await save_sponsor_draft(tg_id, sponsor_data)
    await message.answer(
        t["success_draft"], reply_markup=get_fallback_menu_keyboard(lang)
    )

    # Оповещение администраторам
    for admin_id in ADMINS:
      try:
        admin_text = (
            f"🔔 <b>НОВАЯ АНКЕТА СПОНСОРА (Черновик)</b>\n\n"
            f"👤 Имя: {html.escape(str(sponsor_data['name']))}\n"
            f"🚻 Пол: {html.escape(str(sponsor_data['gender']))}\n"
            f"📅 Возраст: {sponsor_data['age']}\n"
            f"🕊 Трезвость: {html.escape(str(sponsor_data['sobriety']))}\n"
            f"📍 Город: {html.escape(str(sponsor_data['city']))}\n"
            f"📖 Опыт: {html.escape(str(sponsor_data['program_info']))}\n"
            f"✈️ Username: @{message.from_user.username or 'нет'}\n"
            f"📞 Телефон: {html.escape(str(sponsor_data['phone']))}\n"
            f"🆔 ID: {tg_id}"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Одобрить",
                        callback_data=f"approve_sponsor_{tg_id}",
                    ),
                    InlineKeyboardButton(
                        text="❌ Отклонить",
                        callback_data=f"decline_sponsor_{tg_id}",
                    ),
                ]
            ]
        )
        await bot.send_message(
            admin_id, admin_text, reply_markup=keyboard, parse_mode="HTML"
        )
      except Exception as err:
        print(f"Failed to notify admin {admin_id}: {err}")

  except Exception as e:
    print(f"Error saving sponsor draft: {e}")
    traceback.print_exc()
    await message.answer("❌ Произошла ошибка при сохранении анкеты.")

  await state.clear()
