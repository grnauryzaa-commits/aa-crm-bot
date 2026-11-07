"""
Одноразовая миграция: заменяет захардкоженные postgresql:// строки
на импорт DATABASE_URL из db_config.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SELF = Path(__file__).resolve()
SKIP_NAMES = {"db_config.py", "migrate_db_url.py"}

# Ловит: [indent]VAR[: hint] = "postgresql://...";  и  'postgresql://...'
ASSIGN_RE = re.compile(
    r"""^(?P<indent>[ \t]*)
        (?P<var>[A-Za-z_][A-Za-z0-9_]*)
        (?P<hint>\s*:\s*[A-Za-z_][\w\[\]\., ]*)?
        \s*=\s*
        (?P<quote>["'])
        postgresql://[^"']*
        (?P=quote)
        [ \t]*\r?\n?$
    """,
    re.VERBOSE,
)

HOST_HINTS = ("thomas.proxy.rlwy.net", "postgres.railway.internal")


def _find_insert_position(lines: list[str]) -> int:
    i = 0
    n = len(lines)
    while i < n and lines[i].startswith("#"):
        i += 1
    if i < n and lines[i].lstrip().startswith(('"""', "'''")):
        q = lines[i].lstrip()[:3]
        if lines[i].count(q) >= 2:
            i += 1
        else:
            i += 1
            while i < n and q not in lines[i]:
                i += 1
            if i < n:
                i += 1
    last_import = i
    while i < n:
        stripped = lines[i].lstrip()
        if stripped.startswith(("import ", "from ")) or stripped == "" or stripped.startswith("#"):
            if stripped.startswith(("import ", "from ")):
                last_import = i + 1
            i += 1
            continue
        break
    return last_import


def _syspath_preamble(depth: int) -> str:
    if depth == 0:
        return ""
    return (
        "import sys\n"
        "from pathlib import Path as _Path\n"
        f"_ROOT = _Path(__file__).resolve().parents[{depth - 1}]\n"
        "if str(_ROOT) not in sys.path:\n"
        "    sys.path.insert(0, str(_ROOT))\n"
        "\n"
    )


def _patch(path: Path) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    changed = False
    new_lines: list[str] = []
    aliases: list[tuple[str, str]] = []

    for line in lines:
        m = ASSIGN_RE.match(line)
        if not m:
            new_lines.append(line)
            continue
        var = m.group("var")
        if var == "DATABASE_URL":
            aliases.append(("DATABASE_URL", "DATABASE_URL"))
        else:
            aliases.append((var, f"DATABASE_URL as {var}"))
        changed = True
        new_lines.append("\n")

    if not changed:
        return False, "нет совпадений"

    seen: set[str] = set()
    imports: list[str] = []
    for _, imp in aliases:
        if imp not in seen:
            seen.add(imp)
            imports.append(imp)

    depth = len(path.relative_to(ROOT).parts) - 1
    preamble = _syspath_preamble(depth)
    import_block = preamble + "".join(f"from db_config import {imp}\n" for imp in imports)

    insert_at = _find_insert_position(new_lines)
    block = import_block
    if insert_at < len(new_lines) and new_lines[insert_at].strip():
        block = block + "\n"

    new_lines.insert(insert_at, block)
    new_text = "".join(new_lines)

    backup = path.with_suffix(path.suffix + ".bak")
    backup.write_text(text, encoding="utf-8")
    path.write_text(new_text, encoding="utf-8")
    return True, f"импорты: {', '.join(imports)}"


def main() -> int:
    if not (ROOT / "db_config.py").exists():
        print("ОШИБКА: нет db_config.py в корне проекта.")
        return 2

    candidates: list[Path] = []
    for p in ROOT.rglob("*.py"):
        if p.name in SKIP_NAMES:
            continue
        if any(part in {".venv", "venv", "__pycache__", ".git"} for part in p.parts):
            continue
        try:
            txt = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "postgresql://" in txt or any(h in txt for h in HOST_HINTS):
            candidates.append(p)

    if not candidates:
        print("Файлов с postgresql:// не найдено. Всё уже мигрировано?")
        return 0

    print(f"Файлов к обработке: {len(candidates)}\n")
    ok = skipped = 0
    for p in sorted(candidates):
        try:
            changed, msg = _patch(p)
        except Exception as e:
            print(f"[ERR ] {p.relative_to(ROOT)}: {e}")
            skipped += 1
            continue
        tag = "OK  " if changed else "SKIP"
        print(f"[{tag}] {p.relative_to(ROOT)} — {msg}")
        ok += changed
        skipped += not changed

    print(f"\nИтог: изменено {ok}, пропущено {skipped}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())