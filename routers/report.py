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
    try:
        data = await get_report_data()
    except Exception as e:
        await message.answer(f"❌ Ошибка получения данных: {e}")
        return

    total_users = data.get("total_users", 0)
    sponsors = data.get("total_sponsors", 0)
    drafts = data.get("drafts_count", 0)
    normal_users = max(0, total_users - sponsors - drafts)
    
    sponsor_pct = (sponsors / total_users * 100) if total_users else 0
    draft_pct = (drafts / total_users * 100) if total_users else 0
    normal_pct = (normal_users / total_users * 100) if total_users else 0

    text = (
        "📊 <b>СТАТИСТИКА БОТА «NauryzAAbot»</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👥 <b>ПОЛЬЗОВАТЕЛИ</b>\n"
        f"   Всего:                    <b>{total_users}</b>\n"
        f"   ├─ Спонсоры:              <b>{sponsors}</b>  ({sponsor_pct:.0f}%)\n"
        f"   ├─ В модерации:           <b>{drafts}</b>  ({draft_pct:.0f}%)\n"
        f"   └─ Обычные пользователи:  <b>{normal_users}</b>  ({normal_pct:.0f}%)\n\n"
    )

    ru_count = data.get("lang_ru", 0)
    kk_count = data.get("lang_kk", 0)
    ru_pct = (ru_count / total_users * 100) if total_users else 0
    kk_pct = (kk_count / total_users * 100) if total_users else 0
    text += (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n🌐 <b>ЯЗЫКИ ИНТЕРФЕЙСА</b>\n"
        f"   🇷🇺 Русский:               <b>{ru_count}</b>  ({ru_pct:.0f}%)\n"
        f"   🇰🇿 Қазақша:               <b>{kk_count}</b>  ({kk_pct:.0f}%)\n\n"
    )

    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n✍️ <b>СПОНСОРЫ ПО ПОЛУ</b>\n"
    for row in data.get("genders", []):
        if len(row) == 2:
            gender, cnt = row
            g_pct = (cnt / sponsors * 100) if sponsors else 0
            text += f"   {gender}: <b>{cnt}</b>  ({g_pct:.0f}%)\n"
    text += f"   ────────────────────────\n   Всего в базе:             <b>{sponsors}</b>\n\n"

    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n📍 <b>ГЕОГРАФИЯ СПОНСОРОВ</b>\n"
    cities = data.get("cities", [])
    medals = ["🥇", "🥈", "🥉"]
    if not cities: text += "   Нет данных.\n"
    for i, row in enumerate(cities):
        if len(row) == 2:
            city, cnt = row
            medal = medals[i] if i < 3 else "🔹"
            c_pct = (cnt / sponsors * 100) if sponsors else 0
            text += f"   {medal} {city}: <b>{cnt}</b>  ({c_pct:.0f}%)\n"
    text += f"   ────────────────────────\n   Всего в базе:             <b>{sponsors}</b>\n\n"

    monthly_users = data.get("monthly_users", [])
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n📈 <b>РОСТ ПОЛЬЗОВАТЕЛЕЙ</b>\n"
    if not monthly_users:
        text += "   Нет данных за прошлые месяцы.\n"
    else:
        for row in monthly_users:
            if len(row) == 2:
                month, cnt = row
                bar = "█" * min(int(cnt), 15)
                text += f"   {month}:  <b>+{cnt}</b> {bar}\n"
        avg_growth = sum(c for _, c in monthly_users) / len(monthly_users)
        text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n🚀 Темп:  <b>+{avg_growth:.0f} пользователей/месяц</b>\n"

    if total_users:
        text += f"✅ Конверсия:  <b>{sponsor_pct:.0f}%</b> из {total_users} стали спонсорами\n"

    if data.get("action_types"):
        text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔥 <b>ЧТО НАЖИМАЮТ (категории)</b>\n"
        total_act = data.get("total_actions", 0)
        for row in data["action_types"]:
            if len(row) == 2:
                action_type, cnt = row
                names = {"ai_chat": "🤖 ИИ", "menu": "📱 Кнопки меню", "button": "🔘 Inline-кнопки", "command": "⌨️ Команды", "sponsor_form": "📝 Анкеты", "admin": "👑 Админ"}
                pct = (cnt / total_act * 100) if total_act else 0
                text += f"   {names.get(action_type, action_type)}: <b>{cnt}</b> ({pct:.0f}%)\n"

    if data.get("top_actions"):
        text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔥 <b>ТОП НАЖАТИЙ</b>\n"
        total_act = data.get("total_actions", 0)
        for row in data["top_actions"]:
            if len(row) == 3:
                _, action_name, cnt = row
                pct = (cnt / total_act * 100) if total_act else 0
                text += f"   • {action_name}: <b>{cnt}</b> ({pct:.1f}%)\n"

    if data.get("city_activity"):
        text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n🏙 <b>АКТИВНОСТЬ ПО ГОРОДАМ</b>\n"
        for row in data["city_activity"]:
            if len(row) == 2:
                city, cnt = row
                text += f"   {city}: <b>{cnt} действий</b>\n"

    if data.get("ages"):
        text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎂 <b>ВОЗРАСТ СПОНСОРОВ</b>\n"
        for row in data["ages"]:
            if len(row) == 2:
                age_group, cnt = row
                a_pct = (cnt / sponsors * 100) if sponsors else 0
                text += f"   {age_group}: <b>{cnt}</b> ({a_pct:.0f}%)\n"

    await message.answer(text, parse_mode="HTML")