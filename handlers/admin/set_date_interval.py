import re

from datetime import date
from typing import Optional

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

import money
from handlers.admin import AdminStates, get_initial_keyboard
from pkg import dp, get_keyboard, verify_message_is_value, MONEY_VALUE_REGEX_STRING, get_dates_from_string


class SetDateIntervalStates(StatesGroup):
    CHOOSE_ACTION = State()
    WAITING_DATE_BOTTOM = State()
    WAITING_DATE_TOP = State()


FIRST_BUTTON = "Установить временные границы"
BUTTONS = ["Установить нижний порог даты", "Установить верхний порог даты", "Сбросить", "Назад"]


@dp.message_handler(lambda message: message.text==FIRST_BUTTON, state=AdminStates.INITIAL_STATE)
async def choose_action(message: types.Message, state: FSMContext):
    keyboard = get_keyboard(BUTTONS, True)
    text = "Выберите, действие"
    await SetDateIntervalStates.CHOOSE_ACTION.set()
    await message.answer(text, reply_markup=keyboard)


def _parse_date(text: str) -> Optional[date]:
    dates = get_dates_from_string(text)
    if dates:
        return dates[0].date()


@dp.message_handler(lambda message: message.text == BUTTONS[0], state=SetDateIntervalStates.CHOOSE_ACTION)
async def data_bottom(message: types.Message, state: FSMContext):
    await SetDateIntervalStates.WAITING_DATE_BOTTOM.set()
    await message.answer("Введите нижнюю границу даты")


@dp.message_handler(state=SetDateIntervalStates.WAITING_DATE_BOTTOM)
async def data_bottom_value(message: types.Message, state: FSMContext):
    from_date = _parse_date(message.text)
    if not from_date:
        text = f"Вы не ввели дату. Введите нижнюю границу даты"
        await message.answer(text)
        return

    await state.update_data(from_date=from_date)
    text = f"Установил нижнюю границу даты {from_date}"
    await message.answer(text)
    await AdminStates.INITIAL_STATE.set()
    await choose_action(message, state)


@dp.message_handler(lambda message: message.text == BUTTONS[1], state=SetDateIntervalStates.CHOOSE_ACTION)
async def data_top(message: types.Message, state: FSMContext):
    await SetDateIntervalStates.WAITING_DATE_TOP.set()
    await message.answer("Введите верхнюю границу даты")


@dp.message_handler(state=SetDateIntervalStates.WAITING_DATE_TOP)
async def data_top_value(message: types.Message, state: FSMContext):
    to_date = _parse_date(message.text)
    if not to_date:
        text = f"Вы не ввели дату. Введите нижнюю границу даты"
        await message.answer(text)
        return

    await state.update_data(to_date=to_date)
    text = f"Установил верхнюю границу даты {to_date}"
    await AdminStates.INITIAL_STATE.set()
    await message.answer(text)
    await choose_action(message, state)


@dp.message_handler(lambda message: message.text == BUTTONS[2], state=SetDateIntervalStates.CHOOSE_ACTION)
async def reset_dates(message: types.Message, state: FSMContext):
    await state.update_data(from_date=None, to_date=None)
    text = f"Сбросил границы дат"
    await AdminStates.INITIAL_STATE.set()
    await message.answer(text)
    await choose_action(message, state)


@dp.message_handler(lambda message: message.text == BUTTONS[3], state=SetDateIntervalStates.CHOOSE_ACTION)
async def back(message: types.Message, state: FSMContext):
    await AdminStates.INITIAL_STATE.set()
