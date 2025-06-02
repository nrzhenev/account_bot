import asyncio
from typing import List

from aiogram import Router
from aiogram import types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup

import product_storage
from domain.product import ProductVolume
from src.auxiliary.fsm import FSM
from src.handlers.state_messages import StateMessagesHandler
from src.handlers.roles import IsShipmentsRole
from middlewares import AccessMiddleware
from pkg import get_keyboard, ACCESS_IDS


def get_initial_keyboard():
    buttons = INITIAL_BUTTONS
    return get_keyboard(buttons, True)


INITIAL_BUTTONS = ["Ввести поставки от руки"]


# Создаем роутер для обработчиков бармена
barmen_router = Router()
barmen_router.message.middleware(AccessMiddleware(allowed_user_ids=ACCESS_IDS))


class BarmenInitialStates(StatesGroup):
    INITIAL_STATE = State()
    WAITING_CHOOSE_ACTION = State()
    RECIEVE_SHIPMENT_BY_HAND = State()


barmen_mh = StateMessagesHandler()
barmen_fsm = FSM(BarmenInitialStates.INITIAL_STATE.state)

barmen_fsm.add_transition(BarmenInitialStates.INITIAL_STATE.state,
                          BarmenInitialStates.WAITING_CHOOSE_ACTION.state)
barmen_mh.add_state_message(BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND.state, "Выберите действие:")


barmen_fsm.add_transition(BarmenInitialStates.WAITING_CHOOSE_ACTION.state,
                          BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND.state,
                          "Показать поставку")
barmen_mh.add_state_message(BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND.state, "Введите часть названия продукта:")

# Применяем миддлварь проверки роли
barmen_router.message.filter(IsShipmentsRole())


STATES_BY_TEXT = {
    INITIAL_BUTTONS[-1]: BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND
}



def decorator(func):
    async def inside_function(message, state):
        fsm_transition_key = message.text
        barmen_fsm.move(fsm_transition_key)
        await state.set_state(barmen_fsm.state)

        await func(message, state)

        await barmen_mh.handle_set_state(message, state)

    return inside_function



@barmen_router.message(StateFilter(BarmenInitialStates.INITIAL_STATE, None))
@decorator
async def start(message: types.Message, state: FSMContext):
    await asyncio.sleep(0.1)


@barmen_router.message(StateFilter(BarmenInitialStates.WAITING_CHOOSE_ACTION))
@decorator
async def choose_actions(message: types.Message, state: FSMContext):
    return


async def _increments_string(increments: List[ProductVolume]):
    #ps = poster_storage.PosterStorage()
    result = ""
    for inc in increments:
        pid = inc.product_id
        diff = inc.quantity
        product = product_storage.get_product_by_id(pid)
        #product = await ps.product_by_id(pid)
        result += f"{product.name}: {diff} {product.measurement_unit}\n"
    return result


async def _back_handler(message: types.Message, state: FSMContext):
    await state.set_state(BarmenInitialStates.INITIAL_STATE)
    await start(message, state)


PRODUCTS_RANGE = 3


class ReceivingStates(StatesGroup):
    WAITING_SUPPLY_NAME = State()
    WAITING_SUPPLY_QUANTITY = State()
    WAITING_CATEGORY_NAME = State()


def create_range_keyboard(names: List[str]) -> ReplyKeyboardMarkup:
    texts = ["Показать поставку", "Назад", "В начало"]
    keyboard = get_keyboard(names+texts)
    return keyboard
