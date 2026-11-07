"""
Единая точка получения строки подключения к БД.

Источник значения — переменная окружения DATABASE_URL.
Локально она подхватывается из .env (рядом с этим файлом),
на Railway — из Variables сервиса.
"""
from __future__ import annotations

import os
from pathlib import Path

# Загружаем .env, если установлен python-dotenv и файл существует.
# На Railway .env нет — там переменные приходят из окружения.
try:
    from dotenv import load_dotenv

    _ENV_PATH = Path(__file__).resolve().parent / ".env"
    if _ENV_PATH.exists():
        load_dotenv(_ENV_PATH)
except ImportError:
    pass


DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL не задан.\n"
        "Локально: создайте .env рядом с db_config.py (см. .env.example).\n"
        "На Railway: задайте DATABASE_URL в Variables сервиса."
    )

if not DATABASE_URL.startswith(("postgresql://", "postgres://")):
    raise RuntimeError(
        "DATABASE_URL должен начинаться с postgresql:// или postgres://"
    )