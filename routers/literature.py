import logging
from aiogram import F, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_user_language

router = Router()

LITERATURE_RU = [
    {"title": "12 принципов ВМО АА в иллюстрациях", "file_id": "BQACAgIAAxkBAAIelmq2pUr0Zkwiiav_5J0LSydDD7aaAAIspgACwu-xSZoRKFoAASj93D0E"},
    {"title": "12 Шагов АА", "file_id": "BQACAgIAAxkBAAIemGq2pU4hZeaAItX-NHWN3EJtTKI4AAItpgACwu-xSTPQUQxApiILPQQ"},
    {"title": "12 Шагов и 12 Традиций", "file_id": "BQACAgIAAxkBAAIemmq2pU6yw1hZJjlNe6eh_KnEVscjAAIupgACwu-xSUI8p1XYJnp2PQQ"},
    {"title": "44 Вопроса", "file_id": "BQACAgIAAxkBAAIenGq2pU_UAAG7VFt-lYuocdCwK_B1agACL6YAAsLvsUng7ZXIux6gqT0E"},
    {"title": "АА в лечебных учреждениях", "file_id": "BQACAgIAAxkBAAIenmq2pU-DKfmKprjLIHKFZCIcGNpgAAIwpgACwu-xSaPlBFbsaqsqPQQ"},
    {"title": "АА для женщин", "file_id": "BQACAgIAAxkBAAIeoGq2pfUS-xuAWPAEeQbXzNo-4wQ8AAI0pgACwu-xSfEbexGxrOSfPQQ"},
    {"title": "АА с историями", "file_id": "BQACAgIAAxkBAAIeomq2pgcxHGF_AXREwXj92hFoY-ZLAAI1pgACwu-xSR5KPDm5PLUZPQQ"},
    {"title": "Взгляд изнутри", "file_id": "BQACAgIAAxkBAAIeo2q2pggWOgdmkFsnIOaPJJNdTaBWAAI2pgACwu-xSXGRaODrOxJ7PQQ"},
    {"title": "Вопросы о наставничестве", "file_id": "BQACAgIAAxkBAAIepGq2pghyurEKk_rtq5pdeWH18HBHAAI3pgACwu-xSQOJzbelq_ucPQQ"},
    {"title": "Группа АА", "file_id": "BQACAgIAAxkBAAIepWq2pghQ9ueeJBrrhy8J2bltPpiCAAI4pgACwu-xSUlhP3RMAVR9PQQ"},
    {"title": "Доктор Боб и славные ветераны", "file_id": "BQACAgIAAxkBAAIeqmq2pl3HfQoZpyWGHVCRWBP0yYQcAAI7pgACwu-xSUqdqslBYLgHPQQ"},
    {"title": "Думаешь ты особенный", "file_id": "BQACAgIAAxkBAAIerGq2pl6NOQiK2Bp_QAVJl5URBaMQAAI8pgACwu-xSbDh9kFrWmomPQQ"},
    {"title": "Жить трезвыми", "file_id": "BQACAgIAAxkBAAIermq2pmFxBENCA65NCw8JYe--A3zUAAI9pgACwu-xSYxBpjqhXHDOPQQ"},
    {"title": "Завет о Служении АА. Лидерство в АА", "file_id": "BQACAgIAAxkBAAIesGq2pmN6hSscDe2tnN_lkBFLRwlGAAI-pgACwu-xSaC4LGlINNkuPQQ"},
    {"title": "Знакомьтесь: АА", "file_id": "BQACAgIAAxkBAAIesmq2pmZKHA-XPW86PuO56443wOm7AAI_pgACwu-xSWAyajsjwBL0PQQ"},
    {"title": "Лучшие статьи Билла У.", "file_id": "BQACAgIAAxkBAAIetGq2ptSZ7NchzlH7Np8x6WxOU5UOAAJApgACwu-xSelKVWkUn0S7PQQ"},
    {"title": "Молодежь и АА", "file_id": "BQACAgIAAxkBAAIetWq2ptQV21DxRDwfOSn6extGINNpAAJBpgACwu-xSaHN17uDoldFPQQ"},
    {"title": "Новые очки", "file_id": "BQACAgIAAxkBAAIet2q2ptRQxFmX3N-Y01vCiNZT4gABEwACQqYAAsLvsUnOUmc7O1VYVz0E"},
    {"title": "Основные брошюры АА", "file_id": "BQACAgIAAxkBAAIeumq2ptYUnlWWurl_yWHWp7InsMzIAAJDpgACwu-xSdG6BkuNTh7CPQQ"},
    {"title": "Памятка заключенному", "file_id": "BQACAgIAAxkBAAIeu2q2ptcZXfSacAK9tr_5szb1XehgAAJEpgACwu-xSXrLmEiG-d12PQQ"},
    {"title": "Послание женщине-алкоголику", "file_id": "BQACAgIAAxkBAAIevmq2pyvqmWf0yaOGzws1XZszOi_6AAJHpgACwu-xSQX6eSwwpwvHPQQ"},
    {"title": "Руководство обслуживания США и Канады", "file_id": "BQACAgIAAxkBAAIewGq2pyyNwe7QIrSwih08NkMx4p1EAAJIpgACwu-xSTVX6hjILKN0PQQ"},
    {"title": "Руководство по обслуживанию АА России", "file_id": "BQACAgIAAxkBAAIewmq2pyzQ3cGVXwa9W7DCVKfdDWCfAAJJpgACwu-xSSuE33UIevvjPQQ"},
    {"title": "Самообеспечение", "file_id": "BQACAgIAAxkBAAIexGq2py38Kfws9EALqOXuqvx5MIEuAAJKpgACwu-xSa0gdG3XKBC4PQQ"},
    {"title": "Священнослужителям об АА", "file_id": "BQACAgIAAxkBAAIexmq2py2vAVGZJmzKypv-mqXJlHPZAAJLpgACwu-xSbtWFu5avSi5PQQ"},
    {"title": "Традиции АА: как они вырабатывались", "file_id": "BQACAgIAAxkBAAIex2q2py0F-s4b3dmQNsjEYGoFOLSPAAJMpgACwu-xSZIoRNg5XtDlPQQ"},
]

LITERATURE_KK = [
    {"title": "Үлкен кітап", "file_id": "BQACAgIAAxkBAAIfOWq3TEwG8_uzOLPxmEA0W_pe02rbAAIZqwACwu-5SXzmGfa-QkdcPQQ"},
    {"title": "Жаңа көз", "file_id": "BQACAgIAAxkBAAIfOmq3TE1uplAvRYRtfwXqXxvfNyyLAAIaqwACwu-5SWs8rIMhJPVXPQQ"},
    {"title": "Күнделікті ой-толғаулар", "file_id": "BQACAgIAAxkBAAIfPWq3TE7QNT0CI6wp0fGDw4qkC6IxAAIbqwACwu-5SSYCP9_IPN03PQQ"},
    {"title": "Салауатты өмір сүру АА", "file_id": "BQACAgIAAxkBAAIfP2q3TE7QTW1LbvqK9k599uA8sK5KAAIcqwACwu-5SZlA9R6RpHW6PQQ"},
    {"title": "Тас", "file_id": "BQACAgIAAxkBAAIfQGq3TE4jXY27yVvnpPPY31TPLA_lAAIdqwACwu-5Sa9TkjeqtLxUPQQ"},
]

TEXTS = {
    "ru": {
        "choose_lang": "📖 <b>Литература АА</b>\n\nВыберите язык литературы:",
        "btn_ru": "🇷🇺 Русская литература (26)",
        "btn_kk": "🇰🇿 Қазақ әдебиеті (5)",
        "page": "📖 <b>{label}</b> — стр. {page}/{total}",
        "label_ru": "Русская литература АА",
        "label_kk": "Қазақ әдебиеті",
        "back": "⬅️ Назад",
        "forward": "Вперёд ➡️",
        "back_langs": "🌐 К выбору языка",
        "caption": "📖 <b>{title}</b>",
        "empty": "⚠️ Литература пока не загружена.",
    },
    "kk": {
        "choose_lang": "📖 <b>АА Әдебиеті</b>\n\nӘдебиет тілін таңдаңыз:",
        "btn_ru": "🇷🇺 Орыс әдебиеті (26)",
        "btn_kk": "🇰🇿 Қазақ әдебиеті (5)",
        "page": "📖 <b>{label}</b> — {page}/{total} бет",
        "label_ru": "Орыс тіліндегі әдебиет",
        "label_kk": "Қазақ әдебиеті",
        "back": "⬅️ Артқа",
        "forward": "Алға ➡️",
        "back_langs": "🌐 Тіл таңдауға",
        "caption": "📖 <b>{title}</b>",
        "empty": "⚠️ Әдебиет әзірге жүктелмеген.",
    },
}

PER_PAGE = 6


def _books_by_key(key: str):
    if key == "kk":
        return LITERATURE_KK
    return LITERATURE_RU


def _language_menu_kb(lang: str):
    t = TEXTS.get(lang, TEXTS["ru"])
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t["btn_ru"], callback_data="lit_lang_ru"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t["btn_kk"], callback_data="lit_lang_kk"
                )
            ],
        ]
    )
    return keyboard, t["choose_lang"]


def _build_page_keyboard(book_key: str, page: int, interface_lang: str):
    books = _books_by_key(book_key)
    t = TEXTS.get(interface_lang, TEXTS["ru"])
    label = t["label_ru"] if book_key == "ru" else t["label_kk"]

    if not books:
        return None, None

    total = (len(books) + PER_PAGE - 1) // PER_PAGE
    if page < 0:
        page = 0
    if page >= total:
        page = total - 1

    start = page * PER_PAGE
    end = start + PER_PAGE
    page_books = books[start:end]

    keyboard = []
    for i, book in enumerate(page_books):
        real_idx = start + i
        keyboard.append([
            InlineKeyboardButton(
                text=f"📕 {book['title']}",
                callback_data=f"lit_book_{book_key}_{real_idx}",
            )
        ])

    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                text=t["back"],
                callback_data=f"lit_pg_{book_key}_{page - 1}",
            )
        )
    if page < total - 1:
        nav.append(
            InlineKeyboardButton(
                text=t["forward"],
                callback_data=f"lit_pg_{book_key}_{page + 1}",
            )
        )
    if nav:
        keyboard.append(nav)

    keyboard.append([
        InlineKeyboardButton(
            text=t["back_langs"], callback_data="lit_langs"
        )
    ])

    title = t["page"].format(label=label, page=page + 1, total=total)
    return InlineKeyboardMarkup(inline_keyboard=keyboard), title


@router.message(
    F.chat.type == "private",
    F.text.in_({"📖 Литература АА", "📖 АА Әдебиеті"}),
)
async def show_literature(message: types.Message):
    lang = await get_user_language(message.from_user.id) or "ru"
    keyboard, title = _language_menu_kb(lang)
    await message.answer(title, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "lit_langs")
async def back_to_langs(callback: types.CallbackQuery):
    lang = await get_user_language(callback.from_user.id) or "ru"
    keyboard, title = _language_menu_kb(lang)
    try:
        await callback.message.edit_text(
            title, reply_markup=keyboard, parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            title, reply_markup=keyboard, parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("lit_lang_"))
async def show_books_of_lang(callback: types.CallbackQuery):
    book_key = callback.data.split("_")[2]
    if book_key not in ["ru", "kk"]:
        await callback.answer("⚠️ Язык не найден.", show_alert=True)
        return

    lang = await get_user_language(callback.from_user.id) or "ru"
    t = TEXTS.get(lang, TEXTS["ru"])

    books = _books_by_key(book_key)
    if not books:
        await callback.answer(t["empty"], show_alert=True)
        return

    keyboard, title = _build_page_keyboard(book_key, 0, lang)
    try:
        await callback.message.edit_text(
            title, reply_markup=keyboard, parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            title, reply_markup=keyboard, parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("lit_pg_"))
async def literature_page(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    book_key = parts[2]
    page = int(parts[3])

    if book_key not in ["ru", "kk"]:
        await callback.answer("⚠️ Ошибка навигации.", show_alert=True)
        return

    lang = await get_user_language(callback.from_user.id) or "ru"
    keyboard, title = _build_page_keyboard(book_key, page, lang)
    if keyboard is None:
        await callback.answer("⚠️ Список пуст.", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            title, reply_markup=keyboard, parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            title, reply_markup=keyboard, parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("lit_book_"))
async def send_literature(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    book_key = parts[2]
    idx = int(parts[3])

    if book_key not in ["ru", "kk"]:
        await callback.answer("⚠️ Ошибка.", show_alert=True)
        return

    books = _books_by_key(book_key)
    lang = await get_user_language(callback.from_user.id) or "ru"
    t = TEXTS.get(lang, TEXTS["ru"])

    if idx < 0 or idx >= len(books):
        await callback.answer("⚠️ Книга не найдена.", show_alert=True)
        return

    book = books[idx]

    try:
        await callback.message.answer_document(
            document=book["file_id"],
            caption=t["caption"].format(title=book["title"]),
            parse_mode="HTML",
        )
    except Exception as e:
        logging.error(f"Ошибка отправки книги: {e}")
        await callback.answer("⚠️ Не удалось отправить файл.", show_alert=True)
        return

    await callback.answer()