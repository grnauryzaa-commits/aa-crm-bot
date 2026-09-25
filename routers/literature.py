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

LITERATURE_KK = []

TEXTS = {
    "ru": {
        "title": "📖 <b>Литература АА</b>",
        "page": "📖 <b>Литература АА</b> — стр. {page}/{total}",
        "no_books": "⚠️ Литература пока не загружена.",
        "empty_kz": "⚠️ Әзірге қазақ тіліндегі әдебиет жоқ.",
        "back": "⬅️ Назад",
        "forward": "Вперёд ➡️",
        "caption": "📖 <b>{title}</b>",
    },
    "kk": {
        "title": "📖 <b>АА Әдебиеті</b>",
        "page": "📖 <b>АА Әдебиеті</b> — {page}/{total} бет",
        "no_books": "⚠️ Әдебиет әзірге жүктелмеген.",
        "empty_kz": "⚠️ Әзірге қазақ тіліндегі әдебиет жоқ.",
        "back": "⬅️ Артқа",
        "forward": "Алға ➡️",
        "caption": "📖 <b>{title}</b>",
    },
}

PER_PAGE = 6


def _get_books(lang: str):
    if lang == "kk":
        return LITERATURE_KK, "kk"
    return LITERATURE_RU, "ru"


def _build_page_keyboard(lang: str, page: int):
    books, _ = _get_books(lang)
    t = TEXTS.get(lang, TEXTS["ru"])

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
                callback_data=f"lit_{real_idx}_{lang}",
            )
        ])

    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                text=t["back"],
                callback_data=f"lit_page_{page - 1}_{lang}",
            )
        )
    if page < total - 1:
        nav.append(
            InlineKeyboardButton(
                text=t["forward"],
                callback_data=f"lit_page_{page + 1}_{lang}",
            )
        )
    if nav:
        keyboard.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=keyboard), t["page"].format(
        page=page + 1, total=total
    )


@router.message(
    F.chat.type == "private",
    F.text.in_({"📖 Литература АА", "📖 АА Әдебиеті"}),
)
async def show_literature(message: types.Message):
    lang = await get_user_language(message.from_user.id) or "ru"
    t = TEXTS.get(lang, TEXTS["ru"])

    books, _ = _get_books(lang)
    if not books:
        await message.answer(t["empty_kz"] if lang == "kk" else t["no_books"])
        return

    keyboard, title = _build_page_keyboard(lang, 0)
    await message.answer(title, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("lit_page_"))
async def literature_page(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    page = int(parts[2])
    lang = parts[3] if len(parts) > 3 and parts[3] in ["ru", "kk"] else "ru"

    keyboard, title = _build_page_keyboard(lang, page)
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


@router.callback_query(F.data.startswith("lit_") & ~F.data.startswith("lit_page_"))
async def send_literature(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    idx = int(parts[1])
    lang = parts[2] if len(parts) > 2 and parts[2] in ["ru", "kk"] else "ru"

    books, _ = _get_books(lang)
    t = TEXTS.get(lang, TEXTS["ru"])

    if idx < 0 or idx >= len(books):
        await callback.answer("⚠️ Книга не найдена.", show_alert=True)
        return

    book = books[idx]

    await callback.message.answer_document(
        document=book["file_id"],
        caption=t["caption"].format(title=book["title"]),
        parse_mode="HTML",
    )
    await callback.answer()