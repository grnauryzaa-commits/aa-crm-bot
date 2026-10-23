from aiogram import F, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_user_language

router = Router()

SCHEDULE_TEXTS = {
    "ru": {
        "title": "📅 <b>Расписание собраний АА</b>\nВыберите город:",
        "help_text": "\n\nЕсли у вас есть вопросы, нужна поддержка — мы готовы помочь.\n📞 Горячая линия: +7 (707) 208-05-53",
        "back": "⬅️ Назад",
        "2gis": "📍 Открыть в 2GIS",
        "online": "🌐 <b>ОНЛАЙН ГРУППЫ</b>\n\n• <b>Пробуждение</b>: Вт, Чт, Сб 21:00\n<a href='https://us06web.zoom.us/j/82036099070'>Zoom</a> | Пароль: +77754565358\n\n• <b>Бірлік (каз)</b>: Чт 21:00\n<a href='https://us06web.zoom.us/j/7473499478'>Zoom</a> | Пароль: +77074337408\n\n• <b>Шаг за шагом</b>: Вт 19:00\n<a href='https://t.me/+JqgMpZCz_fY1OTVi'>Telegram</a>",
        
        # Тексты городов (списки групп)
        "almaty": "🏙 <b>Группы в Алматы</b>\nВыберите группу:",
        "astana": "🏙 <b>Группы в Астане</b>\nВыберите группу:",
        "aktau": "🏢 <b>Актау</b>\n\n• <b>Парус</b>: 29-й мкр, дом 218, 2-й этаж. Пн, Пт 19:15-20:30.\nТел: +7 777-065-57-97",
        "aktobe": "🏢 <b>Актобе</b>\n\n• <b>ОАЗИС</b>: ул. Абулхаир-Хана 1, 2 этаж, офис 228. Вт, Чт 19:00-20:15; Сб 14:00-15:15.\nТел: +7 747-684-54-24",
        "atyrau": "🏢 <b>Атырау</b>\n\n• <b>Начало</b>: мкр. Авангард-3, 34а. Вт, Чт 19:00-20:30; Сб 12:00-13:30.\nТел: +7 705-449-24-68",
        "karaganda": "🏢 <b>Караганда</b>\n\n• <b>Решение есть</b>: ул. Ерубаева 34. Сб 15:45.\nТел: +7 700-765-69-35",
        "kokshetau": "🏢 <b>Кокшетау</b>\n\n• <b>Синегорье</b>: ул. Ауельбекова 127. Вт, Пт 19:30-20:30.\nТел: +7 771-363-03-02",
        "kostanay": "🏢 <b>Костанай</b>\n\n• <b>Достар</b>: ул. 5 апреля 67, 2 этаж. Пн, Ср, Пт 19:00-20:30. Тел: +7 777-743-56-20\n• <b>12 Шаг</b>: 9 мкр, ул. Генерала Арыстанбекова 23. Вт, Чт 19:00-20:30; Вс 19:00. Тел: +7 777-743-56-20",
        "pavlodar": "🏢 <b>Павлодар</b>\n\n• <b>Крепость</b>: ул. Торайгырова 10/1, 2 этаж, каб. 4. Пн, Ср, Пт 19:00-20:00.\nТел: +7 708-636-15-10",
        "petropavlovsk": "🏢 <b>Петропавловск</b>\n\n• <b>Последняя капля</b>: ул. Букетова 4. Сб 20:00.\nТел: +7 775-827-25-14",
        "rudny": "🏢 <b>Рудный</b>\n\n• <b>Новая свобода</b>: ул. Парковая 55. Ср, Вс 19:30-20:45.\nТел: +7 775-494-79-17",
        "semey": "🏢 <b>Семей</b>\n\n• <b>Семёрочка</b>: Информацию уточнять по телефону.\nТел: +7 707-640-09-13",
        "taldykorgan": "🏢 <b>Талдыкорган</b>\n\n• <b>Жетысу</b>: ул. Шевченко 100. Пн, Ср, Пт 19:00.\nТел: +7 747-629-30-41",
        "oskemen": "🏢 <b>Усть-Каменогорск</b>\n\n• <b>Устье</b>: ул. Казахстан 99. Пн, Ср, Пт 18:00-19:30.\nТел: +7 777-246-79-79",
        "kyzylorda": "🏢 <b>Кызылорда</b>\n\n• <b>Сырдарья</b>: ул. Айтеке би 27А, 2-й этаж, каб. 13. Вт, Чт 19:00; Вс 11:00.\nТел: +7 707-433-74-08",
        "shymkent": "🏢 <b>Шымкент</b>\n\n• <b>Юг</b>: ул. Шаяхметова 14/1. Пн, Ср, Пт 19:00-20:30. Тел: +7 701-674-98-53\n• <b>Шым</b>: ул. Мангельдина 33. Вт, Чт 19:00-20:00; Сб 18:00-19:00. Тел: +7 702-637-23-29\n• <b>Свобода</b>: ул. Московская 9а. Вс 13:00-14:30. Тел: +7 705-990-67-37\n• <b>Пана</b>: ул. Патшайым Тәжібаева 65. Вс 13:00-14:00. Тел: +7 702-637-23-29",
        "ekibastuz": "🏢 <b>Экибастуз</b>\n\n• <b>Чистое Небо</b>: Информацию уточнять по телефону.\nТел: +7 775-350-05-62",
        "zhetysay": "🏢 <b>Жетысай</b>\n\n• <b>Куат</b>: ул. Ауэзова, возле базара Амантай, 2 каб. 12. Пн, Ср, Пт 19:00.\nТел: +7 707-318-38-39",
        "qonaev": "🏢 <b>Конаев</b>\n\n• <b>Надежда</b>: 18 мкр, ул. Курылысшы 8а. Вс 15:00.\nТел: +7 778-166-10-81",
        
        # Тексты групп Алматы
        "alm_zhub": '🏢 <b>Жубанова 3а</b> (между Алтынсарина и Отеген Батыра)\n301 кабинет, 3 этаж (вход справа от гостиницы "Достар")\n\n• <b>Виктория</b>: Вт, Чт 19:30, Сб 19:00\n• <b>Шапагат (каз)</b>: Пн, Ср 19:00, Сб 17:00\n• <b>Чайхана (Новички)</b>: Вс 11:00\n• <b>Женский клуб</b>: Вс 13:00',
        "alm_zenk": "🏢 <b>Зенкова 24 (Дом Офицеров)</b>\n(вход с ул. Калдаякова, по железной лестнице наверх)\n\n• <b>8 марта</b>: Ежедневно 19:00, Вт/Чт 12:00\n• <b>АлмА (Женская)</b>: Сб 12:00\n• <b>ААА (Мужская)</b>: Сб 17:00\n• <b>ВДА</b>: уточнять по контактам",
        "alm_tim": "🏢 <b>Тимирязева 42, корпус 23, каб 102</b>\n\n• <b>Наурыз</b>: Вт, Чт, Пт, Сб 19:00, Вс 15:00",
        "alm_bukhar": "🏢 <b>Бухар Жырау 66, 3 этаж</b> (Zen Studio)\n\n• <b>Друзья Билла</b>: Вт, Чт 12:00-13:00\n• Тел: +7 747-563-75-87",
        "alm_kaskelen": "🏢 <b>ТД «Нур-Жанат» (г. Каскелен)</b>\n\n• <b>Группа «Туран»</b>: Пн, Ср, Сб 17:00–18:15",
        "alm_other": "📍 <b>Другие локации Алматы</b>\n\n• <b>Аксай</b> (Райымбека 493): Вс 13:00\n• <b>НОВЫЕ ОЧКИ</b> (Жибек Жолы 64): Пн, Ср, Пт 19:00, Сб 14:00\n• <b>Боралдай</b> (Курчатова 13а): Сб 17:00\n• <b>Талхиз (Талгар)</b> (Муратбаева 26): Пн, Чт, Пт 19:00\n• <b>Турксиб</b>: Уточнять по тел +77478601105\nВремя: Вт, Чт 19:00-20:30; Вс 17:00-18:30",

        # Тексты групп Астаны
        "ast_petrov": "🏢 <b>ул. Петрова 14/3</b> (вход в подвал с торца «Hada»)\n\n• <b>51 параллель</b>: Ср 19:00-20:15; Сб 15:00-16:15\n• <b>Свобода</b>: Пн, Чт, Пт 19:00-20:00\n• <b>Есиль (каз)</b>: Вс 17:00-18:30",
        "ast_other": "📍 <b>Другие локации Астаны</b>\n\n• <b>Большая перемена</b> (Дукенулы 26): Пн, Пт 19:00-20:00\n• <b>Сана</b> (Кабанбай Батыра 58А): Вт, Чт 20:00-21:15\n• <b>Путь</b> (Ташенова 26): Вт, Ср, Чт 19:00-20:15\n• <b>Возрождение</b> (Куйши Дина 27): Вт 19:00-20:15\n• <b>Гармония</b> (Арасан 2/2): Пн, Пт 19:15\n• <b>Үміт</b> (Шакарима 94): Ср 19:00-20:15\n• <b>Венера</b> (Куйши Дина 27/1): Сб 15:00",

        # Кнопки городов
        "btn_online": "🌐 Онлайн группы",
        "btn_almaty": "🏙 Алматы",
        "btn_astana": "🏙 Астана",
        "btn_aktau": "Актау", "btn_aktobe": "Актобе", "btn_atyrau": "Атырау",
        "btn_karaganda": "Караганда", "btn_kokshetau": "Кокшетау", "btn_kostanay": "Костанай",
        "btn_pavlodar": "Павлодар", "btn_petropavlovsk": "Петропавловск", "btn_rudny": "Рудный",
        "btn_semey": "Семей", "btn_taldykorgan": "Талдыкорган", "btn_oskemen": "Усть-Каменогорск",
        "btn_kyzylorda": "Кызылорда", "btn_shymkent": "Шымкент", "btn_ekibastuz": "Экибастуз",
        "btn_zhetysay": "Жетысай", "btn_qonaev": "Конаев",
        
        # Кнопки групп Алматы и Астаны
        "btn_alm_zhub": "📍 Жубанова 3а", "btn_alm_zenk": "📍 Зенкова 24",
        "btn_alm_tim": "📍 Тимирязева 42 (Наурыз)", "btn_alm_bukhar": "📍 Бухар Жырау 66",
        "btn_alm_kaskelen": "📍 Каскелен: Нур-Жанат", "btn_alm_other": "📍 Другие группы Алматы",
        "btn_ast_petrov": "📍 Петрова 14/3", "btn_ast_other": "📍 Другие группы Астаны",
    },
    
    "kk": {
        "title": "📅 <b>АА жиналыстарының кестесі</b>\nҚаланы таңдаңыз:",
        "help_text": "\n\nЕгер сұрақтарыңыз болса, көмек керек болса — біз көмектесуге дайынбыз.\n📞 Жедел желі: +7 (707) 433-74-08",
        "back": "⬅️ Артқа",
        "2gis": "📍 2GIS-тен ашу",
        "online": "🌐 <b>ОНЛАЙН ТОПТАР</b>\n\n• <b>Пробуждение</b>: Сей, Бей, Сен 21:00\n<a href='https://us06web.zoom.us/j/82036099070'>Zoom</a> | Құпиясөз: +77754565358\n\n• <b>Бірлік</b>: Бей 21:00\n<a href='https://us06web.zoom.us/j/7473499478'>Zoom</a> | Құпиясөз: +77074337408\n\n• <b>Шаг за шагом</b>: Сей 19:00\n<a href='https://t.me/+JqgMpZCz_fY1OTVi'>Telegram</a>",

        "almaty": "🏙 <b>Алматы қаласындағы топтар</b>\nТопты таңдаңыз:",
        "astana": "🏙 <b>Астана қаласындағы топтар</b>\nТопты таңдаңыз:",
        
        "aktau": "🏢 <b>Ақтау</b>\n\n• <b>Парус</b>: 29-шағын аудан, 218-үй. Дс, Жм 19:15-20:30.\nТел: +7 777-065-57-97",
        "aktobe": "🏢 <b>Ақтөбе</b>\n\n• <b>ОАЗИС</b>: Әбілқайыр хан к-сі 1. Сс, Бс 19:00-20:15; Сн 14:00-15:15.\nТел: +7 747-684-54-24",
        "atyrau": "🏢 <b>Атырау</b>\n\n• <b>Начало</b>: Авангард-3, 34а. Сс, Бс 19:00-20:30; Сн 12:00-13:30.\nТел: +7 705-449-24-68",
        "karaganda": "🏢 <b>Қарағанды</b>\n\n• <b>Решение есть</b>: Ерубаев к-сі 34. Сн 15:45.\nТел: +7 700-765-69-35",
        "kokshetau": "🏢 <b>Көкшетау</b>\n\n• <b>Синегорье</b>: Әуелбеков к-сі 127. Сс, Жм 19:30-20:30.\nТел: +7 771-363-03-02",
        "kostanay": "🏢 <b>Қостанай</b>\n\n• <b>Достар</b>: 5 сәуір к-сі 67. Дс, Ср, Жм 19:00-20:30. Тел: +7 777-743-56-20\n• <b>12 Шаг</b>: Арыстанбеков к-сі 23. Сс, Бс 19:00-20:30; Жс 19:00. Тел: +7 777-743-56-20",
        "pavlodar": "🏢 <b>Павлодар</b>\n\n• <b>Крепость</b>: Торайғыров к-сі 10/1. Дс, Ср, Жм 19:00-20:00.\nТел: +7 708-636-15-10",
        "petropavlovsk": "🏢 <b>Петропавл</b>\n\n• <b>Последняя капля</b>: Букетов к-сі 4. Сн 20:00.\nТел: +7 775-827-25-14",
        "rudny": "🏢 <b>Рудный</b>\n\n• <b>Новая свобода</b>: Парковая к-сі 55. Ср, Жс 19:30-20:45.\nТел: +7 775-494-79-17",
        "semey": "🏢 <b>Семей</b>\n\n• <b>Семёрочка</b>: Телефон арқылы нақтылаңыз.\nТел: +7 707-640-09-13",
        "taldykorgan": "🏢 <b>Талдықорған</b>\n\n• <b>Жетысу</b>: Шевченко к-сі 100. Дс, Ср, Жм 19:00.\nТел: +7 747-629-30-41",
        "oskemen": "🏢 <b>Өскемен</b>\n\n• <b>Устье</b>: Қазақстан к-сі 99. Дс, Ср, Жм 18:00-19:30.\nТел: +7 777-246-79-79",
        "kyzylorda": "🏢 <b>Қызылорда</b>\n\n• <b>Сырдарья</b>: Әйтеке би к-сі 27А. Сс, Бс 19:00; Жс 11:00.\nТел: +7 707-433-74-08",
        "shymkent": "🏢 <b>Шымкент</b>\n\n• <b>Юг</b>: Шаяхметов к-сі 14/1. Дс, Ср, Жм 19:00-20:30. Тел: +7 701-674-98-53\n• <b>Шым</b>: Мәңгілік ел к-сі 33. Сс, Бс 19:00-20:00. Тел: +7 702-637-23-29\n• <b>Свобода</b>: Московская к-сі 9а. Жс 13:00-14:30. Тел: +7 705-990-67-37\n• <b>Пана</b>: Тәжібаева к-сі 65. Жс 13:00-14:00. Тел: +7 702-637-23-29",
        "ekibastuz": "🏢 <b>Екібастұз</b>\n\n• <b>Чистое Небо</b>: Телефон арқылы нақтылаңыз.\nТел: +7 775-350-05-62",
        "zhetysay": "🏢 <b>Жетісай</b>\n\n• <b>Куат</b>: Әуезов к-сі. Дс, Ср, Жм 19:00.\nТел: +7 707-318-38-39",
        "qonaev": "🏢 <b>Қонаев</b>\n\n• <b>Надежда</b>: Құрылысшы к-сі 8а. Жс 15:00.\nТел: +7 778-166-10-81",

        "alm_zhub": "🏢 <b>Жұбанов к-сі 3а</b>\n\n• <b>Виктория</b>: Сей, Бей 19:30, Сен 19:00\n• <b>Шапағат</b>: Дүй, Сәр 19:00, Сен 17:00\n• <b>Чайхана</b>: Жек 11:00\n• <b>Әйелдер клубы</b>: Жек 13:00",
        "alm_zenk": "🏢 <b>Зенков к-сі 24</b>\n\n• <b>8 марта</b>: Күн сайын 19:00, Сей/Бей 12:00\n• <b>АлмА</b>: Сен 12:00\n• <b>ААА</b>: Сен 17:00",
        "alm_tim": "🏢 <b>Тимирязев к-сі 42</b>\n\n• <b>Наурыз</b>: Сей, Бей, Жұм, Сен 19:00, Жек 15:00",
        "alm_bukhar": "🏢 <b>Бұхар Жырау к-сі 66</b>\n\n• <b>Друзья Билла</b>: Сей, Бей 12:00-13:00\n• Тел: +7 747-563-75-87",
        "alm_kaskelen": "🏢 <b>«Нұр-Жанат» СҮ (Қаскелен қ.)</b>\n\n• <b>«Тұран» тобы</b>: Дүй, Сәр, Сен 17:00–18:15",
        "alm_other": "📍 <b>Алматыдағы басқа орындар</b>\n\n• <b>Ақсай</b> (Райымбек даңғылы 493): Жек 13:00\n• <b>НОВЫЕ ОЧКИ</b> (Жібек Жолы 64): Дүй, Сәр, Жұм 19:00, Сен 14:00\n• <b>Боралдай</b> (Курчатов 13а): Сен 17:00\n• <b>Талхиз</b> (Мұратбаев 26): Дүй, Бей, Жұм 19:00",
        
        "ast_petrov": "🏢 <b>Петров к-сі 14/3</b>\n\n• <b>51 параллель</b>: Ср 19:00-20:15; Сн 15:00-16:15\n• <b>Свобода</b>: Дс, Бс, Жм 19:00-20:00\n• <b>Есіл</b>: Жс 17:00-18:30",
        "ast_other": "📍 <b>Астанадағы басқа орындар</b>\n\n• <b>Большая перемена</b> (Дүкенұлы 26): Дс, Жм 19:00-20:00\n• <b>Сана</b> (Қабанбай батыр 58А): Сс, Бс 20:00-21:15\n• <b>Путь</b> (Тәшенов 26): Сс, Ср, Бс 19:00-20:15\n• <b>Возрождение</b> (Күйші Дина 27): Сс 19:00-20:15\n• <b>Гармония</b> (Арасан 2/2): Дс, Жм 19:15\n• <b>Үміт</b> (Шәкәрім 94): Ср 19:00-20:15\n• <b>Венера</b> (Күйші Дина 27/1): Сн 15:00",

        "btn_online": "🌐 Онлайн топтар",
        "btn_almaty": "🏙 Алматы",
        "btn_astana": "🏙 Астана",
        "btn_aktau": "Ақтау", "btn_aktobe": "Ақтөбе", "btn_atyrau": "Атырау",
        "btn_karaganda": "Қарағанды", "btn_kokshetau": "Көкшетау", "btn_kostanay": "Қостанай",
        "btn_pavlodar": "Павлодар", "btn_petropavlovsk": "Петропавл", "btn_rudny": "Рудный",
        "btn_semey": "Семей", "btn_taldykorgan": "Талдықорған", "btn_oskemen": "Өскемен",
        "btn_kyzylorda": "Қызылорда", "btn_shymkent": "Шымкент", "btn_ekibastuz": "Екібастұз",
        "btn_zhetysay": "Жетісай", "btn_qonaev": "Қонаев",
        
        "btn_alm_zhub": "📍 Жұбанов 3а", "btn_alm_zenk": "📍 Зенков 24",
        "btn_alm_tim": "📍 Тимирязев 42", "btn_alm_bukhar": "📍 Бұхар Жырау 66",
        "btn_alm_kaskelen": "📍 Қаскелен: Нұр-Жанат", "btn_alm_other": "📍 Алматыдағы басқа топтар",
        "btn_ast_petrov": "📍 Петров 14/3", "btn_ast_other": "📍 Астанадағы басқа топтар",
    },
}

def get_cities_kb(lang="ru"):
    t = SCHEDULE_TEXTS[lang]
    return InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text=t["btn_online"], callback_data="s_online")],
          [InlineKeyboardButton(text=t["btn_almaty"], callback_data="s_city_almaty"),
           InlineKeyboardButton(text=t["btn_astana"], callback_data="s_city_astana")],
          [InlineKeyboardButton(text=t["btn_aktau"], callback_data="s_city_aktau"),
           InlineKeyboardButton(text=t["btn_aktobe"], callback_data="s_city_aktobe")],
          [InlineKeyboardButton(text=t["btn_atyrau"], callback_data="s_city_atyrau"),
           InlineKeyboardButton(text=t["btn_karaganda"], callback_data="s_city_karaganda")],
          [InlineKeyboardButton(text=t["btn_kokshetau"], callback_data="s_city_kokshetau"),
           InlineKeyboardButton(text=t["btn_kostanay"], callback_data="s_city_kostanay")],
          [InlineKeyboardButton(text=t["btn_pavlodar"], callback_data="s_city_pavlodar"),
           InlineKeyboardButton(text=t["btn_petropavlovsk"], callback_data="s_city_petropavlovsk")],
          [InlineKeyboardButton(text=t["btn_rudny"], callback_data="s_city_rudny"),
           InlineKeyboardButton(text=t["btn_semey"], callback_data="s_city_semey")],
          [InlineKeyboardButton(text=t["btn_taldykorgan"], callback_data="s_city_taldykorgan"),
           InlineKeyboardButton(text=t["btn_oskemen"], callback_data="s_city_oskemen")],
          [InlineKeyboardButton(text=t["btn_kyzylorda"], callback_data="s_city_kyzylorda"),
           InlineKeyboardButton(text=t["btn_shymkent"], callback_data="s_city_shymkent")],
          [InlineKeyboardButton(text=t["btn_ekibastuz"], callback_data="s_city_ekibastuz"),
           InlineKeyboardButton(text=t["btn_zhetysay"], callback_data="s_city_zhetysay")],
          [InlineKeyboardButton(text=t["btn_qonaev"], callback_data="s_city_qonaev")],
      ]
  )

def get_almaty_groups_kb(lang="ru"):
    t = SCHEDULE_TEXTS[lang]
    return InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text=t["btn_alm_zhub"], callback_data="s_alm_zhub")],
          [InlineKeyboardButton(text=t["btn_alm_zenk"], callback_data="s_alm_zenk")],
          [InlineKeyboardButton(text=t["btn_alm_tim"], callback_data="s_alm_tim")],
          [InlineKeyboardButton(text=t["btn_alm_bukhar"], callback_data="s_alm_bukhar")],
          [InlineKeyboardButton(text=t["btn_alm_kaskelen"], callback_data="s_alm_kaskelen")],
          [InlineKeyboardButton(text=t["btn_alm_other"], callback_data="s_alm_other")],
          [InlineKeyboardButton(text=t["back"], callback_data="s_back")],
      ]
  )

def get_astana_groups_kb(lang="ru"):
    t = SCHEDULE_TEXTS[lang]
    return InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text=t["btn_ast_petrov"], callback_data="s_ast_petrov")],
          [InlineKeyboardButton(text=t["btn_ast_other"], callback_data="s_ast_other")],
          [InlineKeyboardButton(text=t["back"], callback_data="s_back")],
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
      reply_markup=get_cities_kb(lang),
      parse_mode="HTML",
  )

@router.callback_query(F.data.startswith("s_"))
async def callback_schedule(callback: types.CallbackQuery):
  data = callback.data
  lang = await get_user_language(callback.from_user.id)
  if not lang:
    lang = "ru"

  t = SCHEDULE_TEXTS[lang]
  
  if data == "s_back":
    await callback.message.edit_text(t["title"], reply_markup=get_cities_kb(lang), parse_mode="HTML")
  
  elif data == "s_city_almaty":
    await callback.message.edit_text(t["almaty"], reply_markup=get_almaty_groups_kb(lang), parse_mode="HTML")
      
  elif data == "s_city_astana":
    await callback.message.edit_text(t["astana"], reply_markup=get_astana_groups_kb(lang), parse_mode="HTML")

  elif data == "s_online":
    text = t["online"] + t["help_text"]
    kb = [[InlineKeyboardButton(text=t["back"], callback_data="s_back")]]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML", disable_web_page_preview=True)

  # Обработка городов (кроме Алматы и Астаны, там просто текст)
  elif data.startswith("s_city_"):
    city_key = data.replace("s_city_", "")
    if city_key in t:
        text = t[city_key] + t["help_text"]
        kb = [[InlineKeyboardButton(text=t["back"], callback_data="s_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

  # Обработка групп Алматы
  elif data.startswith("s_alm_"):
    group_key = data.replace("s_", "")
    text = t[group_key] + t["help_text"]
    
    kb = []
    if group_key == "alm_zhub":
        kb.append([InlineKeyboardButton(text=t["2gis"], url="https://2gis.kz/almaty/geo/9430047375041535/76.857015,43.236908")])
    elif group_key == "alm_zenk":
        kb.append([InlineKeyboardButton(text=t["2gis"], url="https://2gis.kz/almaty/geo/70000001112488343")])
    elif group_key == "alm_tim":
        kb.append([InlineKeyboardButton(text=t["2gis"], url="https://2gis.kz/almaty/geo/9430047374971407/76.904347,43.217837")])
    elif group_key == "alm_bukhar":
        kb.append([InlineKeyboardButton(text=t["2gis"], url="https://2gis.kz/almaty/geo/9430047375014586")])
    elif group_key == "alm_kaskelen":
        kb.append([InlineKeyboardButton(text=t["2gis"], url="https://2gis.kz/almaty/geo/70030076201734271/76.642795,43.201247")])
    elif group_key == "alm_other":
        kb.extend([
            [InlineKeyboardButton(text="📍 Новые Очки (2GIS)", url="https://2gis.kz/almaty/geo/9430047374988153/76.950690,43.262199")],
            [InlineKeyboardButton(text="📍 Турксиб (2GIS)", url="https://2gis.kz/almaty/geo/9430047374991567/76.955136,43.330053")],
            [InlineKeyboardButton(text="📍 Талхиз (2GIS)", url="https://2gis.kz/almaty/geo/70000001045475756/77.234246,43.317702")]
        ])
        
    kb.append([InlineKeyboardButton(text=t["back"], callback_data="s_city_almaty")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

  # Обработка групп Астаны
  elif data.startswith("s_ast_"):
    group_key = data.replace("s_", "")
    text = t[group_key] + t["help_text"]
    kb = [[InlineKeyboardButton(text=t["back"], callback_data="s_city_astana")]]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

  await callback.answer()