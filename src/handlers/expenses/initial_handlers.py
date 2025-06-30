import re
from typing import List

import aiogram
from aiogram import Router
from aiogram import types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup
from aiogram.types import KeyboardButton

from middlewares import AccessMiddleware
from pkg import ACCESS_IDS
from pkg import get_keyboard
from src.handlers.roles import IsExpensesRole
from src.handlers.state_messages import MessageHandler, StateWithData

RETURN_BUTTON = "В начало"
BACK_BUTTON = "Назад"
INITIAL_POSSIBILITIES = {"add_expense": "Ввести траты",
                         "increase_debt": "Вернуть/Взять Долг"}


expenses_router = Router()
expenses_router.message.middleware(AccessMiddleware(allowed_user_ids=ACCESS_IDS))


class ExpensesInitialStates(StatesGroup):
    INITIAL_STATE = StateWithData()
    WAITING_CHOOSE_ACTION = StateWithData("Выберите действие:", get_keyboard(["Ввести траты", "Вернуть долг", "Взять в долг"]))
EIS = ExpensesInitialStates

expenses_mh = MessageHandler(EIS.INITIAL_STATE)
expenses_mh.add_transition(EIS.INITIAL_STATE, EIS.WAITING_CHOOSE_ACTION)


def expenses_event(func):
    async def inside_function(message, state):
        result  = await func(message, state)
        if result == -1:
            return

        await expenses_mh.handle_state_transition(message, state)

    return inside_function


def get_initial_keyboard():
    buttons = list(INITIAL_POSSIBILITIES.values())
    return get_keyboard(buttons)


@expenses_router.message(StateFilter(None, EIS.INITIAL_STATE))
@expenses_event
async def expenses_start(message: types.Message, state: FSMContext):
    return


@expenses_router.message(StateFilter(EIS.WAITING_CHOOSE_ACTION))
@expenses_event
async def choose_actions(message: types.Message, state: FSMContext):
    return


def keyboard_with_return_button(names: list):
    return get_keyboard(names + [RETURN_BUTTON])


async def process_quantity(message: types.Message):
    quantity = re.match(r'^[+-]?\d+(\.\d+)?$', message.text)
    if not quantity:
        await message.answer("Введите число в формате 331.12 или 232")
        return
    return float(quantity.group())
