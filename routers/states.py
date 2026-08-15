from aiogram.fsm.state import State, StatesGroup

class SponsorForm(StatesGroup):
    name = State()         # Шаг 1: Имя
    gender = State()       # Шаг 2: Пол
    age = State()          # Шаг 3: Возраст
    sobriety = State()     # Шаг 4: Трезвость
    city = State()         # Шаг 5: Город
    program_info = State() # Шаг 6: Опыт / Программа
    phone = State()        # Шаг 7: Телефон