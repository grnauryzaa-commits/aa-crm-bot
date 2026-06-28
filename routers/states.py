from aiogram.fsm.state import State, StatesGroup

class SponsorForm(StatesGroup):
    gender = State()
    phone = State()
    # добавь другие состояния, если они есть