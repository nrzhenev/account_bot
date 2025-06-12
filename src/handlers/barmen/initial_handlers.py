import asyncio
from typing import List

from aiogram import Router
from aiogram import types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup
from aiogram.types import ReplyKeyboardMarkup

import product_storage
from domain.product import ProductVolume
from src.handlers.state_messages import MessageHandler, StateWithData
from src.handlers.roles import IsShipmentsRole
from middlewares import AccessMiddleware
from pkg import get_keyboard, ACCESS_IDS


INITIAL_BUTTONS = ["Ввести поставки от руки"]
RETURN_BUTTON = "⏮️ (В начало)"
BACK_BUTTON = "◀️ (Назад)"


def get_initial_keyboard():
    buttons = INITIAL_BUTTONS
    return get_keyboard(buttons, True)



# Создаем роутер для обработчиков бармена
barmen_router = Router()
barmen_router.message.middleware(AccessMiddleware(allowed_user_ids=ACCESS_IDS))


class BarmenInitialStates(StatesGroup):
    INITIAL_STATE = StateWithData()
    WAITING_CHOOSE_ACTION = StateWithData("Выберите действие:", get_keyboard(["Ввести поставки", "Отключить ингридиент"]))
    RECIEVE_SHIPMENT_BY_HAND = StateWithData("Введите часть названия продукта:")
    MANAGE_PRODUCTS = StateWithData("Введите часть названия ингридиента, который хотите отключить:")
BIS = BarmenInitialStates


barmen_mh = MessageHandler(BIS.INITIAL_STATE)
barmen_mh.add_transition(BarmenInitialStates.INITIAL_STATE, BarmenInitialStates.WAITING_CHOOSE_ACTION)
barmen_mh.add_transition(BarmenInitialStates.WAITING_CHOOSE_ACTION,
                         BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND,
                          "Ввести поставки")
barmen_mh.add_transition(BarmenInitialStates.WAITING_CHOOSE_ACTION,
                         BarmenInitialStates.MANAGE_PRODUCTS,
                          "Отключить ингридиент")

# Применяем миддлварь проверки роли
barmen_router.message.filter(IsShipmentsRole())


def barmen_event(func):
    async def inside_function(message, state):
        if message.text not in [BACK_BUTTON, RETURN_BUTTON]:
            result  = await func(message, state)
            if result == -1:
                return

        await barmen_mh.handle_state_transition(message, state)

    return inside_function


@barmen_router.message(StateFilter(BarmenInitialStates.INITIAL_STATE, None))
@barmen_event
async def start(message: types.Message, state: FSMContext):
    return 


@barmen_router.message(StateFilter(BarmenInitialStates.WAITING_CHOOSE_ACTION))
@barmen_event
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
        result += f"{product.name}: {diff} {product.unit}\n"
    return result


async def _back_handler(message: types.Message, state: FSMContext):
    await state.set_state(BarmenInitialStates.INITIAL_STATE)
    await start(message, state)


PRODUCTS_RANGE = 3


def create_range_keyboard(names: List[str]) -> ReplyKeyboardMarkup:
    texts = ["Показать поставку", "Назад", "В начало"]
    keyboard = get_keyboard(names+texts)
    return keyboard
