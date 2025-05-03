import re
from typing import List

import aiogram
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import KeyboardButton

from handlers.roles import IsExpensesRole
# import poster_storage
# from poster_storage import PosterStorage, ProductVolume, Product
from pkg import dp


RETURN_BUTTON = "В начало"
INITIAL_POSSIBILITIES = {"add_expense": "Ввести непродуктовые траты",
                         "increase_debt": "Вернуть/Взять Долг"}


__all__ = ['expenses_start_1', 'expenses_start_2']


class ExpensesInitialStates(StatesGroup):
    INITIAL_STATE = State()


def get_keyboard(texts: List[str]):
    keyboard = aiogram.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = [KeyboardButton(text=text) for text in texts]
    keyboard.add(*buttons)
    return keyboard


def get_initial_keyboard():
    buttons = list(INITIAL_POSSIBILITIES.values())
    return get_keyboard(buttons)


@dp.message_handler(IsExpensesRole(), state=None)
async def expenses_start_1(message: types.Message, state: FSMContext):
    await state.reset_state()
    await ExpensesInitialStates.INITIAL_STATE.set()
    keyboard = get_initial_keyboard()
    await message.answer("Выберите действие", reply_markup=keyboard)


@dp.message_handler(IsExpensesRole(), commands=["start"], state="*")
async def expenses_start_2(message: types.Message, state: FSMContext):
    await state.reset_state()
    await ExpensesInitialStates.INITIAL_STATE.set()
    keyboard = get_initial_keyboard()
    await message.answer("Выберите действие", reply_markup=keyboard)


@dp.message_handler(IsExpensesRole(),
                    lambda message: message.text == RETURN_BUTTON,
                    state="*")
async def expenses_start_return(message: types.Message, state: FSMContext):
    await state.reset_state()
    await ExpensesInitialStates.INITIAL_STATE.set()
    keyboard = get_initial_keyboard()
    await message.answer("Выберите действие", reply_markup=keyboard)


def keyboard_with_return_button(names: list):
    keyboard = aiogram.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = [KeyboardButton(text=text) for text in names + [RETURN_BUTTON]]
    return keyboard.add(*buttons)


async def process_quantity(message: types.Message):
    quantity = re.match(r'^[+-]?\d+(\.\d+)?$', message.text)
    if not quantity:
        await message.answer("Введите число в формате 331.12 или 232")
        return
    return float(quantity.group())
