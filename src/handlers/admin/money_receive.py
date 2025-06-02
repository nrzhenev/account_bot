import re

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

import money
from src.handlers.admin import AdminStates, get_initial_keyboard
from src.handlers.roles import IsAdmin
from pkg import dp, verify_message_is_value, MONEY_VALUE_REGEX_STRING


class MoneyReceive(StatesGroup):
    WAITING_RECEPIENT_NAME = State()
    WAITING_RECEIVE_QUANTITY = State()


@dp.message_handler(IsAdmin(), state=MoneyReceive.WAITING_RECEIVE_QUANTITY)
async def products_categories(message: types.Message, state: FSMContext):
    if not await verify_message_is_value(message):
        return

    initial_money = money.get_balance("Счет")
    inc = float(re.search(MONEY_VALUE_REGEX_STRING, message.text).group())
    money.increment("Счет", inc)
    sum = initial_money + inc
    await AdminStates.INITIAL_STATE.set()
    keyboard = get_initial_keyboard()
    await message.answer(f"Добавили {inc} на счет.\nИтого {sum}", reply_markup=keyboard)


@dp.message_handler(IsAdmin(), lambda message: message.text == "Пополнение счета", state="*")
async def products_categories2(message: types.Message, state: FSMContext):
    await MoneyReceive.WAITING_RECEIVE_QUANTITY.set()
    await message.answer("Введите сумму")
