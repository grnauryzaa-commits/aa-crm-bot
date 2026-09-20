from aiogram import F, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_user_language

router = Router()

# Тексты меню расписания для разных языков (с разделением номеров горячей линии)
SCHEDULE_TEXTS = {
    "ru": {
        "title": "📅 <b>Расписание собраний АА</b>\nВыберите локацию:",
        "help_text": (
            "\n\nЕсли у вас есть вопросы, нужна поддержка — мы готовы помочь.\n📞"
            " Горячая линия: +7 (707) 208-05-53"
        ),
        "back": "⬅️ Назад",
        "2gis": "📍 Открыть в 2GIS",
        "online": (
            "🌐 <b>ОНЛАЙН</b>\n\n• <b>Пробуждение</b>: Вт, Чт, Сб 21:00\n<a"
            " href='https://us06web.zoom.us/j/82036099070'>Zoom</a> | Пароль:"
            " +77754565358\n\n• <b>Бірлік (каз)</b>: Чт 21:00\n<a"
            " href='https://us06web.zoom.us/j/7473499478'>Zoom</a> | Пароль:"
            " +77074337408\n\n• <b>Шаг за шагом</b>: Вт 19:00\n<a"
            " href='https://t.me/+JqgMpZCz_fY1OTVi'>Telegram</a>"
        ),
        "zhub": (
            '🏢 <b>Жубанова 3а</b> (между Алтынсарина и Отеген Батыра)\n301 кабинет,'
            ' 3 этаж (вход справа от гостиницы "Достар")\n\n• <b>Виктория</b>: Вт,'
            " Чт 19:30, Сб 19:00\n• <b>Шапагат (каз)</b>: Пн, Ср 19:00, Сб 17:00\n•"
            " <b>Чайхана (Новички)</b>: Вс 11:00\n• <b>Женский клуб</b>: Вс 13:00"
        ),
        "zenk": (
            "🏢 <b>Зенкова 24 (Дом Офицеров)</b>\n(вход с ул. Калдаякова, по"
            " железной лестнице наверх)\n\n• <b>8 марта</b>: Ежедневно 19:00,"
            " Вт/Чт 12:00\n• <b>АлмА (Женская)</b>: Сб 12:00\n• <b>ААА (Мужская)</b>:"
            " Сб 17:00\n• <b>ВДА</b>: уточнять по контактам"
        ),
        "tim": (
            "🏢 <b>Тимирязева 42, корпус 23, каб 102</b>\n\n• <b>Друзья"
            " Билла</b>: Вт, Чт 12:00\n• <b>Наурыз</b>: Вт, Чт, Пт, Сб 19:00, Вс"
            " 15:00"
        ),
        "kaskelen": (
            "🏢 <b>ТД «Нур-Жанат» (г. Каскелен)</b>\n\n• <b>Группа «Туран»</b>: Пн,"
            " Ср, Сб 17:00–18:15"
        ),
        "other": (
            "📍 <b>Другие локации</b>\n\n• <b>Аксай</b> (Райымбека 493): Вс"
            " 13:00\n• <b>НОВЫЕ ОЧКИ</b> (Жибек Жолы 64): Пн, Ср, Пт 19:00, Сб"
            " 14:00\n• <b>Боралдай</b> (Курчатова 13а): Сб 17:00\n• <b>Талхиз"
            " (Талгар)</b> (Муратбаева 26): Пн, Чт, Пт 19:00\n\n• <b>Турксиб</b>:"
            " Уточнять по тел +77478601105\nВремя: Вт, Чт 19:00-20:30; Вс"
            " 17:00-18:30"
        ),
        "btn_online": "🌐 Онлайн группы",
        "btn_zhub": "📍 Алматы: Жубанова 3а",
        "btn_zenk": "📍 Алматы: Зенкова 24",
        "btn_tim": "📍 Алматы: Тимирязева 42",
        "btn_kaskelen": "📍 Каскелен: Нур-Жанат",
        "btn_other": "📍 Другие локации",
    },
    "kk": {
        "title": "📅 <b>АА жиналыстарының кестесі</b>\nОрынды таңдаңыз:",
        "help_text": (
            "\n\nЕгер сұрақтарыңыз болса, көмек керек болса — біз көмектесуге"
            " дайынбыз.\n📞 Жедел желі: +7 (707) 433-74-08"
        ),
        "back": "⬅️ Артқа",
        "2gis": "📍 2GIS-тен ашу",
        "online": (
            "🌐 <b>ОНЛАЙН</b>\n\n• <b>Пробуждение</b>: Сей, Бей, Сен 21:00\n<a"
            " href='https://us06web.zoom.us/j/82036099070'>Zoom</a> | Құпиясөз:"
            " +77754565358\n\n• <b>Бірлік (каз)</b>: Бей 21:00\n<a"
            " href='https://us06web.zoom.us/j/7473499478'>Zoom</a> | Құпиясөз:"
            " +77074337408\n\n• <b>Шаг за шагом</b>: Сей 19:00\n<a"
            " href='https://t.me/+JqgMpZCz_fY1OTVi'>Telegram</a>"
        ),
        "zhub": (
            '🏢 <b>Жұбанов көшесі, 3а</b> (Алтынсарин мен Өтеген батыр'
            ' аралығы)\n301 кабинет, 3 қабат ("Достар" қонақүйінің оң жақ'
            " кіреберісі)\n\n• <b>Виктория</b>: Сей, Бей 19:30, Сен 19:00\n• <b>Шапағат"
            " (қаз)</b>: Дүй, Сәр 19:00, Сен 17:00\n• <b>Чайхана (Жаңадан"
            " келгендер)</b>: Жек 11:00\n• <b>Әйелдер клубы</b>: Жек 13:00"
        ),
        "zenk": (
            "🏢 <b>Зенков көшесі, 24 (Офицерлер үйі)</b>\n(Қалдаяқов көшесі жағынан"
            " кіреберіс, темір баспалдақпен жоғары)\n\n• <b>8 марта</b>: Күн сайын"
            " 19:00, Сей/Бей 12:00\n• <b>АлмА (Әйелдер)</b>: Сен 12:00\n•"
            " <b>ААА (Ерлер)</b>: Сен 17:00\n• <b>ВДА</b>: байланыс нөмірлері"
            " арқылы нақтылау"
        ),
        "tim": (
            "🏢 <b>Темірғазин/Тимирязев 42, 23-корпус, 102-каб</b>\n\n• <b>Друзья"
            " Билла</b>: Сей, Бей 12:00\n• <b>Наурыз</b>: Сей, Бей, Жұм, Сен 19:00,"
            " Жек 15:00"
        ),
        "kaskelen": (
            "🏢 <b>«Нур-Жанат» СҮ (Қаскелен қ.)</b>\n\n• <b>«Тұран» тобы</b>: Дүй,"
            " Сәр, Сен 17:00–18:15"
        ),
        "other": (
            "📍 <b>Басқа орындар</b>\n\n• <b>Ақсай</b> (Райымбек 493): Жек"
            " 13:00\n• <b>НОВЫЕ ОЧКИ</b> (Жібек Жолы 64): Дүй, Сәр, Жұм 19:00, Сен"
            " 14:00\n• <b>Боралдай</b> (Курчатов 13а): Сен 17:00\n• <b>Талхиз"
            " (Талғар)</b> (Мұратбаев 26): Дүй, Бей, Жұм 19:00\n\n•"
            " <b>Турксиб</b>: +77478601105 арқылы нақтылау\nУақыты: Сей, Бей"
            " 19:00-20:30; Жек 17:00-18:30"
        ),
        "btn_online": "🌐 Онлайн топтар",
        "btn_zhub": "📍 Алматы: Жұбанов 3а",
        "btn_zenk": "📍 Алматы: Зенков 24",
        "btn_tim": "📍 Алматы: Темірғазин 42",
        "btn_kaskelen": "📍 Қаскелен: Нұр-Жанат",
        "btn_other": "📍 Басқа орындар",
    },
}


def get_schedule_menu_kb(lang="ru"):
  t = SCHEDULE_TEXTS[lang]
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text=t["btn_online"], callback_data="s_online")],
          [InlineKeyboardButton(text=t["btn_zhub"], callback_data="s_zhub")],
          [InlineKeyboardButton(text=t["btn_zenk"], callback_data="s_zenk")],
          [InlineKeyboardButton(text=t["btn_tim"], callback_data="s_tim")],
          [
              InlineKeyboardButton(
                  text=t["btn_kaskelen"], callback_data="s_kaskelen"
              )
          ],
          [InlineKeyboardButton(text=t["btn_other"], callback_data="s_other")],
      ]
  )


@router.message(
    F.chat.type == "private", F.text.in_({"📅 Расписание", "📅 Кесте"})
)
async def show_schedule_menu(message: types.Message):
  lang = await get_user_language(message.from_user.id)
  if not lang:
    lang = "ru"
  await message.answer(
      SCHEDULE_TEXTS[lang]["title"],
      reply_markup=get_schedule_menu_kb(lang),
      parse_mode="HTML",
  )


@router.callback_query(F.data.startswith("s_"))
async def callback_schedule(callback: types.CallbackQuery):
  data = callback.data
  lang = await get_user_language(callback.from_user.id)
  if not lang:
    lang = "ru"

  t = SCHEDULE_TEXTS[lang]
  kb_back = [[InlineKeyboardButton(text=t["back"], callback_data="s_back")]]

  if data == "s_back":
    await callback.message.edit_text(
        t["title"], reply_markup=get_schedule_menu_kb(lang), parse_mode="HTML"
    )

  elif data == "s_online":
    text = t["online"] + t["help_text"]
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_back),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

  elif data == "s_zhub":
    text = t["zhub"] + t["help_text"]
    kb = [
        [
            InlineKeyboardButton(
                text=t["2gis"],
                url=(
                    "https://2gis.kz/almaty/geo/9430047375041535/76.857015,43.236908"
                ),
            )
        ],
        [InlineKeyboardButton(text=t["back"], callback_data="s_back")],
    ]
    await callback.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML"
    )

  elif data == "s_zenk":
    text = t["zenk"] + t["help_text"]
    kb = [
        [
            InlineKeyboardButton(
                text=t["2gis"],
                url="https://2gis.kz/almaty/geo/70000001112488343",
            )
        ],
        [InlineKeyboardButton(text=t["back"], callback_data="s_back")],
    ]
    await callback.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML"
    )

  elif data == "s_tim":
    text = t["tim"] + t["help_text"]
    kb = [
        [
            InlineKeyboardButton(
                text=t["2gis"],
                url=(
                    "https://2gis.kz/almaty/geo/9430047374971407/76.904347,43.217837"
                ),
            )
        ],
        [InlineKeyboardButton(text=t["back"], callback_data="s_back")],
    ]
    await callback.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML"
    )

  elif data == "s_kaskelen":
    text = t["kaskelen"] + t["help_text"]
    kb = [
        [
            InlineKeyboardButton(
                text=t["2gis"],
                url=(
                    "https://2gis.kz/almaty/geo/70030076201734271/76.642795,43.201247"
                ),
            )
        ],
        [InlineKeyboardButton(text=t["back"], callback_data="s_back")],
    ]
    await callback.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML"
    )

  elif data == "s_other":
    text = t["other"] + t["help_text"]
    kb = [
        [
            InlineKeyboardButton(
                text="📍 Новые Очки (2GIS)",
                url=(
                    "https://2gis.kz/almaty/geo/9430047374988153/76.950690,43.262199"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                text="📍 Турксиб (2GIS)",
                url=(
                    "https://2gis.kz/almaty/geo/9430047374991567/76.955136,43.330053"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                text="📍 Талхиз (2GIS)",
                url=(
                    "https://2gis.kz/almaty/geo/70000001045475756/77.234246,43.317702"
                ),
            )
        ],
        [InlineKeyboardButton(text=t["back"], callback_data="s_back")],
    ]
    await callback.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML"
    )

  await callback.answer()