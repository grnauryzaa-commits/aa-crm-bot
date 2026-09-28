# -*- coding: utf-8 -*-
"""
Прямая загрузка размышлений в PostgreSQL через psycopg2.
Никаких SQL-файлов, никаких проблем с апострофами.
"""
import re
import psycopg2
from docx import Document

# ← ВСТАВЬ СВОЙ DATABASE_URL из Railway (тот же, что в config.py)
DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"

DOCX_PATH = "reflections_kz.docx"

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
    if not t or len(t) > 200:
        return False
    markers = [
        "Анонимді Алкоголиктер", "Alcoholics Anonymous",
        "Он Екі Қадам", "Twelve Steps", "As Bill Sees It",
        "Биллдің көзқарасы", "Биллдің көз қарасы",
        "Доктор Боб", "Жүректің тілі", "The Language of the Heart",
        "AA Comes of Age", "АА есейеді", "Grapevine",
        "-бет", "–бет",
    ]
    for marker in markers:
        if marker in t:
            return True
    return False


def parse_entries(paragraphs):
    entries = []
    current_month = None
    day_in_month = 0
    seen_days = set()
    month_first_seen = set()

    i = 0
    n = len(paragraphs)

    while i < n:
        para = paragraphs[i]
        month_ru, rest = extract_month_and_title(para)
        if not month_ru:
            i += 1
            continue

        # Маркер месяца — первый раз
        if month_ru not in month_first_seen:
            month_first_seen.add(month_ru)
            current_month = month_ru
            day_in_month = 0
            i += 1
            continue

        # Смена месяца
        if month_ru != current_month:
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


def main():
    print("📖 Читаю reflections_kz.docx...")
    paragraphs = load_paragraphs(DOCX_PATH)
    print(f"   Всего абзацев: {len(paragraphs)}")

    print("🔍 Парсю записи...")
    entries = parse_entries(paragraphs)
    print(f"   Найдено записей: {len(entries)}")

    print("🔌 Подключаюсь к PostgreSQL...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    print("🗑  Удаляю старые записи...")
    cur.execute("DELETE FROM reflections;")

    print("📥 Загружаю новые записи...")
    for e in entries:
        cur.execute(
            "INSERT INTO reflections (day, month, title, text) "
            "VALUES (%s, %s, %s, %s)",
            (e["day"], e["month"], e["title"], e["text"]),
        )

    conn.commit()
    print(f"✅ Загружено {len(entries)} записей")

    cur.close()
    conn.close()
    print("🎉 Готово!")


if __name__ == "__main__":
    main()