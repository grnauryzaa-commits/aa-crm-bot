import traceback
import html
import psycopg2
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
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

# Словари локализации для анкеты и списков (русский / казахский)
FORM_TEXTS = {
    "ru": {
        "btn_become": "➕ Стать спонсором",
        "menu_title": (
            "➕ <b>Стать спонсором в АА</b>\n\nСпонсор — это человек, который"
            " прошел Шаги и готов делиться опытом с другими. Если вы"
            " чувствуете в себе силы и имеете устойчивую трезвость, вы можете"
            " зарегистрироваться как спонсор."
        ),
        "btn_fill": "📝 Заполнить анкету спонсора",
        "ask_name": "👤 Напиши свое имя:",
        "ask_gender": "Какой твой пол? (Брат / Сестра)",
        "ask_age": "📅 Напиши свой возраст (цифрой):",
        "ask_sobriety": "🕊 Какой у тебя срок трезвости? (например: 3 года 2 месяца)",
        "ask_city": "📍 Из какого ты города?",
        "ask_program": (
            "📖 Напиши коротко о своем опыте по программе / спонсорстве:"
        ),
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
        "user_declined": (
            "❌ К сожалению, ваша анкета спонсора была отклонена."
        ),
        "fallback_become": "➕ Стать спонсором",
        "fallback_list": "📋 Список спонсоров",
        "fallback_main": "🏠 Главное меню",
        "choose_list": "👥 Выберите список:",
        "empty_list": "Список {label} пока пуст.",
        "not_found": "⚠️ Спонсор не найден в базе данных.",
        "access_denied": "⚠️ Вы можете редактировать только свою анкету!",
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
            "➕ <b>АА-да демеуші болу</b>\n\nДемеуші — Қадамдардан өткен және"
            " басқалармен тәжірибе бөлісуге дайын адам. Егер сіз өзіңізде күш"
            " сезінсеңіз және тұрақты тазалық мерзіміңіз болса, демеуші ретінде"
            " тіркеле аласыз."
        ),
        "btn_fill": "📝 Демеуші сауалнамасын толтыру",
        "ask_name": "👤 Атыңызды жазыңыз:",
        "ask_gender": "Жынысыңыз қандай? (Бауыр / Әпке)",
        "ask_age": "📅 Жасыңызды жазыңыз (санмен):",
        "ask_sobriety": (
            "🕊 Тазалық мерзіміңіз қандай? (мысалы: 3 жыл 2 ай)"
        ),
        "ask_city": "📍 Қай қаладансыз?",
        "ask_program": (
            "📖 Бағдарлама/демеушілік тәжірибеңіз туралы қысқаша жазыңыз:"
        ),
        "ask_phone": "📞 Байланыс үшін телефон нөміріңізді жазыңыз:",
        "success_draft": (
            "✅ Сіздің сауалнамаңыз әкімшіге модерацияға сәтті жіберілді!"
        ),
        "admin_title": "🔔 ДЕМЕУШІНІ ТІРКЕУ ӨТІНІШІ",
        "admin_approve": "✅ Карточканы мақұлдау",
        "admin_decline": "❌ Бас тарту",
        "approved_alert": "Сауалнама мақұлданды!",
        "declined_alert": "Сауалнама қабылданбады.",
        "user_approved": (
            "🎉 Құттықтаймыз! Сіздің демеуші сауалнамаңыз мақұлданды."
        ),
        "user_declined": (
            "❌ Өкінішке орай, сіздің демеуші сауалнамаңыз қабылданбады."
        ),
        "fallback_become": "➕ Демеуші болу",
        "fallback_list": "📋 Демеушілер тізімі",
        "fallback_main": "🏠 Басты мәзір",
        "choose_list": "👥 Тізімді таңдаңыз:",
        "empty_list": "{label} тізімі әзірге бос.",
        "not_found": "⚠️ Демеуші деректер базасынан табылмады.",
        "access_denied": "⚠️ Сіз тек өз сауалнамаңызды өңдей аласыз!",
        "btn_brothers": "👦 Бауырлар",
        "btn_sisters": "👧 Әпкелер",
        "btn_back": "⬅️ Артқа",
        "btn_forward": "Алға ➡️",
        "btn_edit": "✏️ Сауалнаманы өңдеу",
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


# --- ПЕРЕХВАТ КНОПКИ СТАТЬ СПОНСОРОМ ---
@router.message(
    F.text.in_({"➕ Стать спонсором", "➕ Демеуші болу"})
    | F.text.contains("Демеуші")
    | F.text.contains("Спонсор")
)
async def start_form_text(message: Message, state: FSMContext):
  try:
    text_lower = message.text.lower() if message.text else ""
    if "демеуші" in text_lower:
      lang = "kk"
    else:
      lang = await get_user_language(message.from_user.id)
      if not lang:
        lang = "ru"

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
    print(f"Ошибка в start_form_text: {e}")
    traceback.print_exc()


# --- МЕНЮ СПОНСОРОВ (СПИСКИ БРАТЬЕВ И СЕСТЕР) ---
@router.message(
    F.text.in_({"🤝 Спонсоры", "🤝 Демеушілер"})
    | F.text.contains("Демеушілер")
    | F.text.contains("Спонсоры")
)
@router.callback_query(
    F.data == "menu_sponsors" or F.data.startswith("menu_sponsors_")
)
async def sponsors_menu(event: Message | CallbackQuery):
  user_id = event.from_user.id
  if isinstance(event, Message) and event.text and "Демеушілер" in event.text:
    lang = "kk"
  elif isinstance(event, CallbackQuery) and event.data.endswith("_kk"):
    lang = "kk"
  else:
    lang = await get_user_language(user_id)
    if not lang:
      lang = "ru"

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
    F.data.startswith(("list_brothers_", "list_sisters_"))
)
async def show_list_page(callback: CallbackQuery):
  parts = callback.data.split("_")
  list_type = parts[1]
  page = int(parts[2])
  lang = parts[3] if len(parts) > 3 else "ru"

  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  gender_filter = (
      "OR gender ILIKE '%муж%'"
      if list_type == "brothers"
      else "OR gender ILIKE '%жен%'"
  )

  # Правильный выбор локализованной метки для заголовка
  label = t["label_brothers"] if list_type == "brothers" else t["label_sisters"]
  db_keyword = "брат" if list_type == "brothers" else "сестр"

  try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        f"SELECT user_id, name, age, city, sobriety FROM sponsors WHERE gender"
        f" ILIKE '%{db_keyword}%' {gender_filter};"
    )
    all_sponsors = cur.fetchall()
    cur.close()
    conn.close()
  except Exception as e:
    print(f"Ошибка БД в show_list_page: {e}")
    all_sponsors = []

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
    city_name = city if city else t["default_city"]
    button_text = f"{name}, {age} | {city_name} | {sobriety}"
    keyboard.append([
        InlineKeyboardButton(
            text=button_text,
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

  await callback.message.edit_text(
      f"📖 ({label}) — {page + 1} / {total_pages}:",
      reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
  )


@router.callback_query(F.data.startswith("view_sp_"))
async def show_details(callback: CallbackQuery):
  parts = callback.data.split("_")
  user_id = parts[2]
  list_type = parts[3]
  page = parts[4]
  lang = parts[5] if len(parts) > 5 else "ru"

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
    print(f"Ошибка БД в show_details: {e}")
    sp = None

  if sp:
    name, gender, age, sobriety, city, username, phone, program_info = sp
    tg_contact = (
        f"@{username}"
        if username and username not in ("-", "нет")
        else f"ID: {user_id}"
    )

    if lang == "kk":
      text = (
          f"👤 Демеуші: {name} ({gender}), {age}\n🕊 Трэзвость мерзімі: {sobriety}\n📍"
          f" Қала: {city}\n📖 Тәжірибе: {program_info}\n✈️ Telegram:"
          f" {tg_contact}\n📞 Телефон: {phone}"
      )
    else:
      text = (
          f"👤 Спонсор: {name} ({gender}), {age}\n🕊 Трезвость: {sobriety}\n📍"
          f" Город: {city}\n📖 Опыт: {program_info}\n✈️ Telegram:"
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

    await callback.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
  else:
    await callback.answer(t["not_found"], show_alert=True)


# --- ЗАПОЛНЕНИЕ АНКЕТЫ С СОХРАНЕНИЕМ ЯЗЫКА ---
@router.callback_query(F.data.startswith("start_sponsor_registration"))
async def start_form_callback(callback: CallbackQuery, state: FSMContext):
  try:
    parts = callback.data.split("_")
    lang = parts[3] if len(parts) > 3 else None

    if not lang:
      lang = await get_user_language(callback.from_user.id)
      if not lang:
        lang = "ru"

    await state.update_data(lang=lang)
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

    await callback.message.answer(
        t["ask_name"], reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(SponsorForm.name)
    await callback.answer()
  except Exception as e:
    print(f"CRITICAL ERROR в start_form_callback: {e}")
    traceback.print_exc()
    try:
      await callback.answer("Ошибка при запуске анкеты.", show_alert=True)
    except:
      pass


@router.message(SponsorForm.name)
async def process_name(message: Message, state: FSMContext):
  data = await state.get_data()
  lang = data.get("lang", "ru")
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  await state.update_data(name=message.text)
  await message.answer(t["ask_gender"])
  await state.set_state(SponsorForm.gender)


@router.message(SponsorForm.gender)
async def process_gender(message: Message, state: FSMContext):
  data = await state.get_data()
  lang = data.get("lang", "ru")
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  await state.update_data(gender=message.text)
  await message.answer(t["ask_age"])
  await state.set_state(SponsorForm.age)


@router.message(SponsorForm.age)
async def process_age(message: Message, state: FSMContext):
  data = await state.get_data()
  lang = data.get("lang", "ru")
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  await state.update_data(age=message.text)
  await message.answer(t["ask_sobriety"])
  await state.set_state(SponsorForm.sobriety)


@router.message(SponsorForm.sobriety)
async def process_sobriety(message: Message, state: FSMContext):
  data = await state.get_data()
  lang = data.get("lang", "ru")
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  await state.update_data(sobriety=message.text)
  await message.answer(t["ask_city"])
  await state.set_state(SponsorForm.city)


@router.message(SponsorForm.city)
async def process_city(message: Message, state: FSMContext):
  data = await state.get_data()
  lang = data.get("lang", "ru")
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  await state.update_data(city=message.text)
  await message.answer(t["ask_program"])
  await state.set_state(SponsorForm.program_info)


@router.message(SponsorForm.program_info)
async def process_program_info(message: Message, state: FSMContext):
  data = await state.get_data()
  lang = data.get("lang", "ru")
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  await state.update_data(program_info=message.text)
  await message.answer(t["ask_phone"])
  await state.set_state(SponsorForm.phone)


@router.message(SponsorForm.phone)
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
  except Exception as e:
    print(f"Ошибка сохранения черновика в БД: {e}")

  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text=t["admin_approve"],
                  callback_data=f"approve_sp_{tg_id}",
              ),
              InlineKeyboardButton(
                  text=t["admin_decline"],
                  callback_data=f"decline_sp_{tg_id}",
              ),
          ]
      ]
  )

  admin_text = (
      f"🔔 {t['admin_title']}\n"
      "━━━━━━━━━━━━━━━━━━\n"
      f"👤 Имя: {html.escape(str(sponsor_data['name']))} ({html.escape(str(sponsor_data['gender']))})\n"
      f"📅 Возраст: {html.escape(str(sponsor_data['age']))}\n"
      f"🕊 Трезвость: {html.escape(str(sponsor_data['sobriety']))}\n"
      f"📍 Город: {html.escape(str(sponsor_data['city']))}\n\n"
      f"📖 Опыт/Программа: {html.escape(str(sponsor_data['program_info']))}\n"
      f"✈️ Telegram: @{html.escape(str(sponsor_data['username']))}\n"
      f"📞 Телефон: {html.escape(str(sponsor_data['phone']))}\n"
      "━━━━━━━━━━━━━━━━━━"
  )

  for admin_id in ADMINS:
    try:
      await bot.send_message(
          chat_id=admin_id,
          text=admin_text,
          reply_markup=keyboard,
          parse_mode="HTML",
      )
    except Exception as e:
      print(f"Не удалось отправить админу {admin_id}: {e}")

  await message.answer(
      t["success_draft"], reply_markup=get_fallback_menu_keyboard(lang)
  )
  await state.clear()


# --- МОДЕРАЦИЯ АДМИНИСТРАТОРОМ ---
@router.callback_query(F.data.startswith("approve_sp_"))
async def approve_sponsor(callback: CallbackQuery, bot: Bot):
  target_user_id = int(callback.data.split("_")[2])
  lang = await get_user_language(target_user_id)
  if not lang:
    lang = "ru"
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        "SELECT name, gender, age, sobriety, city, username, phone,"
        " program_info FROM sponsor_drafts WHERE user_id = %s;",
        (target_user_id,),
    )
    draft = cur.fetchone()

    if draft:
      cur.execute(
          """
                INSERT INTO sponsors (user_id, name, gender, age, sobriety, city, username, phone, program_info)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    name = EXCLUDED.name, gender = EXCLUDED.gender, age = EXCLUDED.age,
                    sobriety = EXCLUDED.sobriety, city = EXCLUDED.city, username = EXCLUDED.username,
                    phone = EXCLUDED.phone, program_info = EXCLUDED.program_info;
            """,
          (target_user_id, *draft),
      )

      cur.execute(
          "DELETE FROM sponsor_drafts WHERE user_id = %s;", (target_user_id,)
      )
      conn.commit()

    cur.close()
    conn.close()

    await callback.message.edit_text(
        f"{callback.message.text}\n\n✅ ОДОБРЕНО АДМИНИСТРАТОРОМ", reply_markup=None
    )
    await callback.answer(t["approved_alert"])

    try:
      await bot.send_message(target_user_id, t["user_approved"])
    except:
      pass

  except Exception as e:
    print(f"Ошибка в approve: {e}")
    await callback.answer("Ошибка БД", show_alert=True)


@router.callback_query(F.data.startswith("decline_sp_"))
async def decline_sponsor(callback: CallbackQuery, bot: Bot):
  target_user_id = int(callback.data.split("_")[2])
  lang = await get_user_language(target_user_id)
  if not lang:
    lang = "ru"
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM sponsor_drafts WHERE user_id = %s;", (target_user_id,))
    conn.commit()
    cur.close()
    conn.close()

    await callback.message.edit_text(
        f"{callback.message.text}\n\n❌ ОТКЛОНЕНО АДМИНИСТРАТОРОМ",
        reply_markup=None,
    )
    await callback.answer(t["declined_alert"])

    try:
      await bot.send_message(target_user_id, t["user_declined"])
    except:
      pass
  except Exception as e:
    print(f"Ошибка в decline: {e}")
    await callback.answer("Ошибка БД", show_alert=True)