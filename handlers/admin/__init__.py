from aiogram.dispatcher.filters.state import StatesGroup, State

from pkg import get_keyboard


class AdminStates(StatesGroup):
    INITIAL_STATE = State()


def get_initial_keyboard():
    return get_keyboard(["balance", "expenses", "set price", "Пополнение счета", "storage_history", "storage", "Перевести деньги",
                         "История действий", "История денег", "Установить временные границы"])
