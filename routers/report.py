# routers/report.py
from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command

from config import ADMINS
from database import get_report_data

router = Router()


@router.message(Command("report"))
async def cmd_report(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer("Эта команда только для администраторов.")
        return

    await message.answer("⏳ Собираю данные...")

    data = await get_report_data()

    total_users = data["total_users"]
    total_sponsors = data["total_sponsors"]
    drafts = data["drafts_count"]
    total_actions = data["total_actions"]

    # Конверсия в спонсоров
    sponsor_pct = (
        (total_sponsors / total_users * 100) if total_users else 0
    )
    draft_pct = (drafts / total_users * 100) if total_users else 0

    text = "📊 <b>ОТЧЁТ ПО БОТУ</b>\n"
    text += f"🗓 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"

    text += "<b>👥 Пользователи</b>\n"
    text += f"• Всего: <b>{total_users}</b>\n"
    text += f"• Активных за 7 дней: <b>{data['active_week']}</b>\n\n"

    text += "<b>🖱 Активность</b>\n"
    text += f"• Всего действий: <b>{total_actions}</b>\n"
    text += f"• Запросов к ИИ за 7 дней: <b>{data['ai_week']}</b>\n\n"

    text += "<b>🤝 Спонсоры</b>\n"
    text += f"• Стали спонсорами: <b>{total_sponsors}</b> ({sponsor_pct:.1f}%)\n"
    text += f"• Черновиков: <b>{drafts}</b> ({draft_pct:.1f}%)\n\n"

    if data["top_actions"]:
        text += "<b>🔥 Топ-15 действий</b>\n"
        for action_type, action_name, cnt in data["top_actions"]:
            pct = (cnt / total_actions * 100) if total_actions else 0
            text += (
                f"• [{action_type}] {action_name}: "
                f"<b>{cnt}</b> ({pct:.1f}%)\n"
            )
        text += "\n"

    if data["cities"]:
        text += "<b>🌍 Топ-10 городов спонсоров</b>\n"
        for city, cnt in data["cities"]:
            pct = (cnt / total_sponsors * 100) if total_sponsors else 0
            text += f"• {city}: <b>{cnt}</b> ({pct:.1f}%)\n"
        text += "\n"

    if data["genders"]:
        text += "<b>⚧ Пол спонсоров</b>\n"
        for gender, cnt in data["genders"]:
            pct = (cnt / total_sponsors * 100) if total_sponsors else 0
            text += f"• {gender}: <b>{cnt}</b> ({pct:.1f}%)\n"
        text += "\n"

    if data["ages"]:
        text += "<b>🎂 Возраст спонсоров</b>\n"
        for age_group, cnt in data["ages"]:
            pct = (cnt / total_sponsors * 100) if total_sponsors else 0
            text += f"• {age_group}: <b>{cnt}</b> ({pct:.1f}%)\n"

    await message.answer(text, parse_mode="HTML")