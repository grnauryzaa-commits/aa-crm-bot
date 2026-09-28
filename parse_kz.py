# -*- coding: utf-8 -*-
"""
Парсер казахских ежедневных размышлений из reflections_kz.docx.
"""
import re
from docx import Document

DOCX_PATH = "reflections_kz.docx"
OUTPUT_SQL = "reflections_kz.sql"

MONTHS_ORDER = [
    "Январь", "Февраль", "Март", "Апрель",
    "Май", "Июнь", "Июль", "Август",
    "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]

MONTH_KZ_TO_RU = {
    "қаңтар": "Январь",
    "ақпан": "Февраль",
    "наурыз": "Март",
    "сәуір": "Апрель",
    "мамыр": "Май",
    "маусым": "Июнь",
    "шілде": "Июль",
    "тамыз": "Август",
    "қыркүйек": "Сентябрь",
    "қазан": "Октябрь",
    "қараша": "Ноябрь",
    "желтоқсан": "Декабрь",
}

MONTH_REGEX = re.compile(
    r"^(қаңтар|ақпан|наурыз|сәуір|мамыр|маусым|"
    r"шілде|тамыз|қыркүйек|қазан|қараша|желтоқсан)\b",
    flags=re.IGNORECASE | re.UNICODE,
)


def load_paragraphs(path: str):
    doc = Document(path)
    return [p.text.strip() for p in doc.paragraphs]


def extract_month_and_title(paragraph: str, max_rest_len: int = 100):
    """Возвращает (month_ru, rest) или (None, None)."""
    stripped = paragraph.strip()
    if not stripped:
        return None, None

    m = MONTH_REGEX.match(stripped)
    if not m:
        return None, None

    month_kz = m.group(1).lower()
    month_ru = MONTH_KZ_TO_RU.get(month_kz)
    if not month_ru:
        return None, None

    rest = stripped[m.end():].strip(" .,-–—")

    if len(rest) > max_rest_len:
        return None, None

    return month_ru, rest


def is_probable_title(text: str) -> bool:
    if not text:
        return False

    t = text.strip(" .,-–—")

    if (t.startswith("«") and t.endswith("»")) or (
        t.startswith('"') and t.endswith('"')
    ):
        return True

    letters = re.findall(r"[А-ЯЁӘҒҚҢӨҰҮҺІA-Z]", t)
    if len(letters) >= 3:
        lowercase = re.findall(r"[а-яёәғқңөұүһіa-z]", t)
        if len(lowercase) == 0:
            return True

    return False


def is_source_line(text: str) -> bool:
    t = text.strip()
    if not t:
        return False

    if len(t) > 200:
        return False

    markers = [
        "Анонимді Алкоголиктер",
        "Alcoholics Anonymous",
        "Он Екі Қадам",
        "Twelve Steps",
        "As Bill Sees It",
        "Биллдің көзқарасы",
        "Биллдің көз қарасы",
        "Доктор Боб",
        "Жүректің тілі",
        "The Language of the Heart",
        "AA Comes of Age",
        "АА есейеді",
        "Grapevine",
        "-бет",
        "–бет",
    ]

    for marker in markers:
        if marker in t:
            return True

    return False


def parse_entries(paragraphs, debug=False):
    """
    Возвращает список записей: [{month, day, title, text}, ...]

    Логика:
      - Маркер месяца = ПЕРВОЕ появление названия месяца в документе
        (или сразу после предыдущего месяца), БЕЗ текста в той же строке
        и следующий абзац НЕ начинается с того же месяца.
      - Все остальные появления месяца — это дни.
    """
    entries = []
    current_month = None
    day_in_month = 0
    seen_days = set()
    month_first_seen = set()  # какие месяцы уже встречались

    i = 0
    n = len(paragraphs)

    while i < n:
        para = paragraphs[i]
        month_ru, rest = extract_month_and_title(para)

        if not month_ru:
            i += 1
            continue

        # --- Это первое появление месяца в документе → МАРКЕР ---
        if month_ru not in month_first_seen:
            month_first_seen.add(month_ru)
            current_month = month_ru
            day_in_month = 0
            if debug:
                print(f"  ⏭ Маркер месяца: {month_ru} (i={i})")
            i += 1
            continue

        # --- Это день внутри текущего месяца ---
        if month_ru != current_month:
            # Месяц сменился впервые → это новый месяц → маркер
            current_month = month_ru
            day_in_month = 0
            i += 1
            continue

        day_in_month += 1

        title = rest if rest else ""
        text_parts = []

        j = i + 1
        while j < n:
            next_para = paragraphs[j]
            next_month, _ = extract_month_and_title(next_para)
            if next_month:
                break

            if is_source_line(next_para):
                j += 1
                continue

            if not next_para.strip():
                j += 1
                continue

            if not title and is_probable_title(next_para):
                title = next_para.strip().strip("«»\"")
                j += 1
                continue

            text_parts.append(next_para.strip())
            j += 1

        text = "\n\n".join(text_parts).strip()

        if not title and not text:
            day_in_month -= 1
            if debug:
                print(f"  ⏭ Пустая запись: {month_ru} день {day_in_month + 1}")
            i = j
            continue

        key = (month_ru, day_in_month)
        if key not in seen_days:
            seen_days.add(key)
            entries.append({
                "month": month_ru,
                "day": day_in_month,
                "title": title,
                "text": text,
            })

        i = j

    return entries


def escape_sql(s: str) -> str:
    # Убираем все виды апострофов и заменяем на прямые двойные кавычки
    if s is None:
        return ""
    s = s.replace("'", "''")             # прямой апостроф U+0027
    s = s.replace("\u2019", "''")        # ’ типографский
    s = s.replace("\u2018", "''")        # ‘ типографский
    s = s.replace("\u02BC", "''")        # ʼ модификатор
    s = s.replace("\u0060", "''")        # ` обратный апостроф
    return s


def generate_sql(entries, path):
    lines = []
    lines.append("-- Автоматически сгенерировано из reflections_kz.docx")
    lines.append("DELETE FROM reflections;")
    lines.append("")

    for e in entries:
        day = e["day"]
        month = escape_sql(e["month"])
        title = escape_sql(e["title"])
        text = escape_sql(e["text"])

        lines.append(
            f"INSERT INTO reflections (day, month, title, text) "
            f"VALUES ({day}, '{month}', '{title}', '{text}');"
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    print("📖 Читаю reflections_kz.docx...")
    paragraphs = load_paragraphs(DOCX_PATH)
    print(f"   Всего абзацев: {len(paragraphs)}")

    print("🔍 Парсю записи...")
    entries = parse_entries(paragraphs, debug=True)

    by_month = {}
    for e in entries:
        by_month.setdefault(e["month"], 0)
        by_month[e["month"]] += 1

    print("\n📊 Записей по месяцам:")
    for m in MONTHS_ORDER:
        print(f"   {m}: {by_month.get(m, 0)}")

    print(f"\n✅ Всего записей: {len(entries)}")

    print("\n📅 Сводка по месяцам:")
    for m in MONTHS_ORDER:
        days = [e for e in entries if e["month"] == m]
        if days:
            min_d = min(d["day"] for d in days)
            max_d = max(d["day"] for d in days)
            print(f"   {m}: min={min_d}, max={max_d}, count={len(days)}")

    print("\n📋 Первые 5 записей каждого месяца:")
    for m in MONTHS_ORDER:
        days = sorted(
            [e for e in entries if e["month"] == m],
            key=lambda x: x["day"],
        )[:5]
        print(f"\n   {m}:")
        for e in days:
            print(f"     день {e['day']}: {e['title'][:60]}")

    print("\n💾 Генерирую SQL...")
    generate_sql(entries, OUTPUT_SQL)
    print(f"📄 SQL-файл: {OUTPUT_SQL}")


if __name__ == "__main__":
    main()