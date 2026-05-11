from aiogram.fsm.state import StatesGroup, State


class SponsorForm(StatesGroup):
    name = State()
    age = State()
    identity = State()
    sobriety = State()
    city = State()
    formats = State()
    telegram = State()
    phone = State()
    about = State()