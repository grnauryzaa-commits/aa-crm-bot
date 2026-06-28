from aiogram.fsm.state import State, StatesGroup

class SponsorForm(StatesGroup):
    gender = State()   # Шаг 1: Пол
    phone = State()    # Шаг 2: Телефон