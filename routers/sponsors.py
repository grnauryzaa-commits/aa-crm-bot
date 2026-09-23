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
from database import get_user_language

router = Router()


# Состояния для пошагового заполнения новой анкеты
class SponsorForm(StatesGroup):
  name = State()
  gender = State()
  age = State()
  sobriety = State()
  city = State()
  program_info = State()
  phone = State()


# Тексты интерфейса
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
        "edit_menu_title": (
            "✏️ <b>Редактирование анкеты</b>\n\nВыберите поле, которое хотите"
            " изменить:"
        ),
        "edit_name_btn": "👤 Имя",
        "edit_gender_btn": "🚻 Пол",
        "edit_age_btn": "📅 Возраст",
        "edit_sobriety_btn": "🕊 Трезвость",
        "edit_city_btn": "📍 Город",
        "edit_program_btn": "📖 Опыт",
        "edit_phone_btn": "📞 Телефон",
        "field_updated": "✅ Поле успешно изменено!",
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
            "✅ Сіздің сауалнамаңыз әкімшіге модерацияға жіберілді!"
        ),
        "admin_title": "🔔 ДЕМЕУШІНІ ТІРКЕУ ӨТІНІШІ",
        "admin_approve": "✅ Карточканы мақұлдау",
        "admin_decline": "❌ Бас тарту",
        "approved_alert": "Сауалнама мақұлданды!",
        "declined_alert": "Сауалнама қабылданбады.",
        "user_declined": (
            "❌ Өкінішке орай, сіздің демеуші сауалнамаңыз қабылданбады."
        ),
        "user_approved": (
            "🎉 Құттықтаймыз! Сіздің демеуші сауалнамаңыз мақұлданды."
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
        "edit_menu_title": (
            "✏️ <b>Сауалнаманы өңдеу</b>\n\nӨзгерткіңіз келетін өрісті"
            " таңдаңыз:"
        ),
        "edit_name_btn": "👤 Аты",
        "edit_gender_btn": "🚻 Жынысы",
        "edit_age_btn": "📅 Жасы",
        "edit_sobriety_btn": "🕊 Тазалық",
        "edit_city_btn": "📍 Қаласы",
        "edit_program_btn": "📖 Тәжірибесі",
        "edit_phone_btn": "📞 Телефон",
        "field_updated": "✅ Өріс сәтті өзгертілді!",
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
    F.chat.type == "private",
    F.text.in_({"➕ Стать спонсором", "➕ Демеуші болу"}),
)
async def start_form_text(message: Message, state: FSMContext):
  try:
    lang = await get_user_language(message.from_user.id)
    if not lang:
      lang = "ru"

    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM sponsors WHERE user_id = %s UNION SELECT 1 FROM"
        " sponsor_drafts WHERE user_id = %s;",
        (message.from_user.id, message.from_user.id),
    )
    is_sponsor = cur.fetchone()
    cur.close()
    conn.close()

    keyboard_buttons = [
        [
            InlineKeyboardButton(
                text=t["btn_fill"],
                callback_data=f"start_sponsor_registration_{lang}",
            )
        ]
    ]

    if is_sponsor:
      keyboard_buttons.append([
          InlineKeyboardButton(
              text=t["btn_edit"], callback_data=f"open_edit_menu_{lang}"
          )
      ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.answer(
        t["menu_title"], reply_markup=keyboard, parse_mode="HTML"
    )
  except Exception as e:
    print(f"Ошибка в start_form_text: {e}")
    traceback.print_exc()


# --- ЗАПУСК ПОШАГОВОГО ЗАПОЛНЕНИЯ АНКЕТЫ ---
@router.callback_query(F.data.startswith("start_sponsor_registration_"))
async def start_sponsor_registration(
    callback: CallbackQuery, state: FSMContext
):
  lang = callback.data.split("_")[-1]
  if lang not in ["ru", "kk"]:
    lang = "ru"

  await state.update_data(lang=lang)
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  await callback.message.answer(
      t["ask_name"], reply_markup=ReplyKeyboardRemove()
  )
  await state.set_state(SponsorForm.name)
  await callback.answer()


@router.message(SponsorForm.name)
async def process_sponsor_name(message: Message, state: FSMContext):
  await state.update_data(name=message.text.strip())
  data = await state.get_data()
  lang = data.get("lang", "ru")
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  keyboard = ReplyKeyboardMarkup(
      keyboard=[
          [
              KeyboardButton(text="Брат" if lang == "ru" else "Бауыр"),
              KeyboardButton(text="Сестра" if lang == "ru" else "Әпке"),
          ]
      ],
      resize_keyboard=True,
      one_time_keyboard=True,
  )
  await message.answer(t["ask_gender"], reply_markup=keyboard)
  await state.set_state(SponsorForm.gender)


@router.message(SponsorForm.gender)
async def process_sponsor_gender(message: Message, state: FSMContext):
  await state.update_data(gender=message.text.strip())
  data = await state.get_data()
  lang = data.get("lang", "ru")
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  await message.answer(t["ask_age"], reply_markup=ReplyKeyboardRemove())
  await state.set_state(SponsorForm.age)


@router.message(SponsorForm.age)
async def process_sponsor_age(message: Message, state: FSMContext):
  await state.update_data(age=message.text.strip())
  data = await state.get_data()
  lang = data.get("lang", "ru")
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  await message.answer(t["ask_sobriety"], reply_markup=ReplyKeyboardRemove())
  await state.set_state(SponsorForm.sobriety)


@router.message(SponsorForm.sobriety)
async def process_sponsor_sobriety(message: Message, state: FSMContext):
  await state.update_data(sobriety=message.text.strip())
  data = await state.get_data()
  lang = data.get("lang", "ru")
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  await message.answer(t["ask_city"], reply_markup=ReplyKeyboardRemove())
  await state.set_state(SponsorForm.city)


@router.message(SponsorForm.city)
async def process_sponsor_city(message: Message, state: FSMContext):
  await state.update_data(city=message.text.strip())
  data = await state.get_data()
  lang = data.get("lang", "ru")
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  await message.answer(t["ask_program"], reply_markup=ReplyKeyboardRemove())
  await state.set_state(SponsorForm.program_info)


@router.message(SponsorForm.program_info)
async def process_sponsor_program(message: Message, state: FSMContext):
  await state.update_data(program_info=message.text.strip())
  data = await state.get_data()
  lang = data.get("lang", "ru")
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

  await message.answer(t["ask_phone"], reply_markup=ReplyKeyboardRemove())
  await state.set_state(SponsorForm.phone)


@router.message(SponsorForm.phone)
async def process_sponsor_phone(message: Message, state: FSMContext, bot: Bot):
  await state.update_data(phone=message.text.strip())
  data = await state.get_data()
  user_id = message.from_user.id
  lang = data.get("lang", "ru")
  t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])
  username = message.from_user.username or "нет"

  name = data.get("name", "Не указано")
  gender = data.get("gender", "Не указано")
  age = str(data.get("age", "0"))
  sobriety = data.get("sobriety", "Не указано")
  city = data.get("city", "Не указано")
  program_info = data.get("program_info", "Не указано")
  phone = data.get("phone", message.text.strip())

  try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        """
            INSERT INTO sponsor_drafts (user_id, name, gender, age, sobriety, city, username, phone, program_info)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                name = EXCLUDED.name, 
                gender = EXCLUDED.gender, 
                age = EXCLUDED.age,
                sobriety = EXCLUDED.sobriety, 
                city = EXCLUDED.city, 
                username = EXCLUDED.username,
                phone = EXCLUDED.phone, 
                program_info = EXCLUDED.program_info;
        """,
        (
            user_id,
            name,
            gender,
            age,
            sobriety,
            city,
            username,
            phone,
            program_info,
        ),
    )
    conn.commit()
    cur.close()
    conn.close()
  except Exception as e:
    print(f"Ошибка сохранения анкеты в БД: {e}")
    traceback.print_exc()

  await message.answer(
      t["success_draft"], reply_markup=get_fallback_menu_keyboard(lang)
  )
  await state.clear()

  for admin_id in ADMINS:
    try:
      admin_text = (
          f"🔔 <b>ЗАЯВКА НА РЕГИСТРАЦИЮ СПОНСОРА</b>\n\n"
          f"👤 Имя: {name}\n"
          f"🚻 Пол: {gender}\n"
          f"📅 Возраст: {age}\n"
          f"🕊 Трезвость: {sobriety}\n"
          f"📍 Город: {city}\n\n"
          f"📖 Опыт: {program_info}\n"
          f"✈️ Telegram: @{username if username != 'нет' else 'нет'}\n"
          f"📞 Телефон: {phone}"
      )
      kb = InlineKeyboardMarkup(
          inline_keyboard=[[
              InlineKeyboardButton(
                  text=t["admin_approve"], callback_data=f"approve_sp_{user_id}"
              ),
              InlineKeyboardButton(
                  text=t["admin_decline"], callback_data=f"reject_sp_{user_id}"
              ),
          ]]
      )
      await bot.send_message(admin_id, admin_text, reply_markup=kb)
    except Exception as e:
      print(f"Не удалось отправить заявку админу {admin_id}: {e}")


# --- МЕНЮ СПОНСОРОВ (СПИСКИ БРАТЬЕВ И СЕСТЕР) ---
@router.message(
    F.chat.type == "private", F.text.in_({"🤝 Спонсоры", "🤝 Демеушілер"})
)
async def sponsors_menu_msg(message: Message):
  user_id = message.from_user.id
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
  await message.answer(t["choose_list"], reply_markup=keyboard)


@router.callback_query(
    (F.data == "menu_sponsors") | (F.data.startswith("menu_sponsors_"))
)
async def sponsors_menu_cb(callback: CallbackQuery):
  if callback.message.chat.type != "private":
    await callback.answer()
    return
  user_id = callback.from_user.id

  parts = callback.data.split("_")
  lang = parts[3] if len(parts) > 3 and parts[3] in ["ru", "kk"] else None
  if not lang:
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
  try:
    await callback.message.edit_text(t["choose_list"], reply_markup=keyboard)
  except Exception:
    await callback.message.answer(t["choose_list"], reply_markup=keyboard)
  await callback.answer()


@router.callback_query(F.data.startswith("list_"))
async def show_list_page(callback: CallbackQuery):
  if callback.message.chat.type != "private":
    await callback.answer()
    return
  parts = callback.data.split("_")
  if len(parts) < 3:
    await callback.answer("Ошибка навигации", show_alert=True)
    return

  list_type = parts[1]
  page = int(parts[2])

  lang = parts[3] if len(parts) > 3 and parts[3] in ["ru", "kk"] else None
  if not lang:
    lang = await get_user_language(callback.from_user.id)
    if not lang:
      lang = "ru"

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
    print(f"Ошибка БД в show_list_page: {e}")
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


# --- ПРОСМОТР ДЕТАЛЕЙ КОНКРЕТНОГО СПОНСОРА ---
@router.callback_query(F.data.startswith("view_sp_"))
async def show_details(callback: CallbackQuery):
  if callback.message.chat.type != "private":
    await callback.answer()
    return
  parts = callback.data.split("_")
  user_id = parts[2]
  list_type = parts[3]
  page = parts[4]
  lang = parts[5] if len(parts) > 5 and parts[5] in ["ru", "kk"] else None
  if not lang:
    lang = await get_user_language(callback.from_user.id)
    if not lang:
      lang = "ru"

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

  if not sp:
    await callback.answer(t["not_found"], show_alert=True)
    return

  name, gender, age, sobriety, city, username, phone, program_info = sp
  city_name = city if city else t["default_city"]

  details_text = (
      f"👤 <b>Имя:</b> {name}\n"
      f"🚻 <b>Пол:</b> {gender}\n"
      f"📅 <b>Возраст:</b> {age}\n"
      f"🕊 <b>Трезвость:</b> {sobriety}\n"
      f"📍 <b>Город:</b> {city_name}\n\n"
      f"📖 <b>Опыт:</b> {program_info}\n\n"
      f"✈️ <b>Telegram:</b> @{username if username and username != 'нет' else 'нет'}\n"
      f"📞 <b>Телефон:</b> {phone}"
  )

  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text=t["btn_back"],
              callback_data=f"list_{list_type}_{page}_{lang}",
          )
      ]]
  )

  await callback.message.edit_text(
      details_text, reply_markup=keyboard, parse_mode="HTML"
  )
  await callback.answer()


# --- АДМИНСКАЯ МОДЕРАЦИЯ (ОДОБРИТЬ / ОТКЛОНИТЬ) ---
@router.callback_query(F.data.startswith("approve_sp_"))
async def approve_sponsor(callback: CallbackQuery, bot: Bot):
  if callback.from_user.id not in ADMINS:
    await callback.answer("У вас нет прав администратора.", show_alert=True)
    return

  user_id = callback.data.split("_")[2]

  try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        "SELECT name, gender, age, sobriety, city, username, phone,"
        " program_info FROM sponsor_drafts WHERE user_id = %s;",
        (user_id,),
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
          (user_id, *draft),
      )
      cur.execute("DELETE FROM sponsor_drafts WHERE user_id = %s;", (user_id,))
      conn.commit()

    cur.close()
    conn.close()

    lang = await get_user_language(int(user_id)) or "ru"
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

    await bot.send_message(int(user_id), t["user_approved"])
    await callback.message.edit_text(
        f"{callback.message.text}\n\n<b>✅ ОДОБРЕНО</b>"
    )
    await callback.answer("Успешно одобрено!")
  except Exception as e:
    print(f"Ошибка при одобрении спонсора: {e}")
    traceback.print_exc()
    await callback.answer("Ошибка при обработке запроса.", show_alert=True)


@router.callback_query(F.data.startswith("reject_sp_"))
async def reject_sponsor(callback: CallbackQuery, bot: Bot):
  if callback.from_user.id not in ADMINS:
    await callback.answer("У вас нет прав администратора.", show_alert=True)
    return

  user_id = callback.data.split("_")[2]

  try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM sponsor_drafts WHERE user_id = %s;", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    lang = await get_user_language(int(user_id)) or "ru"
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

    await bot.send_message(int(user_id), t["user_declined"])
    await callback.message.edit_text(
        f"{callback.message.text}\n\n<b>❌ ОТКЛОНЕНО</b>"
    )
    await callback.answer("Анкета отклонена.")
  except Exception as e:
    print(f"Ошибка при отклонении спонсора: {e}")
    await callback.answer("Ошибка при обработке запроса.", show_alert=True)
