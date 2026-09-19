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

# Словари локализации для анкеты (русский / казахский)
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
    F.text.in_({"➕ Стать спонсором", "➕ Демеуші болу"})
)
async def start_form_text(message: Message, state: FSMContext):
  try:
    lang = await get_user_language(message.from_user.id)
    t = FORM_TEXTS.get(lang, FORM_TEXTS["ru"])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t["btn_fill"], callback_data="start_sponsor_registration"
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


@router.callback_query(F.data == "start_sponsor_registration")
async def start_form_callback(callback: CallbackQuery, state: FSMContext):
  try:
    lang = await get_user_language(callback.from_user.id)
    
    # Страховка для корректного определения языка по тексту кнопки
    if callback.message.reply_markup:
        for row in callback.message.reply_markup.inline_keyboard:
            for btn in row:
                if btn.callback_data == "start_sponsor_registration" and "толтыру" in btn.text.lower():
                    lang = "kk"

    # Жёстко фиксируем язык в стейте на время всей анкеты
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


@router.callback_query(F.data.startswith("approve_sp_"))
async def approve_sponsor(callback: CallbackQuery, bot: Bot):
  target_user_id = int(callback.data.split("_")[2])
  lang = await get_user_language(target_user_id)
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