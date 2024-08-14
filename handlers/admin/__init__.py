from aiogram import types
from aiogram.dispatcher.filters.state import StatesGroup, State

from handlers.roles import IsAdmin
from pkg import get_keyboard, dp


class AdminStates(StatesGroup):
    INITIAL_STATE = State()


def get_initial_keyboard():
    return get_keyboard(["balance", "expenses", "set price", "Пополнение счета", "storage_history", "storage", "Перевести деньги",
                         "История действий", "История денег", "Установить временные границы"])


@dp.message_handler(IsAdmin(), state=None)
async def get_initial_message(message: types.Message):
    keyboard = get_initial_keyboard()
    await AdminStates.INITIAL_STATE.set()
    await message.answer("Выберите действие", reply_markup=keyboard)
