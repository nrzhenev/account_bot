from typing import List

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

import product_storage
from domain.product import ProductVolume

from handlers.roles import IsShipmentsRole
from pkg import get_keyboard, ACCESS_IDS
from middlewares import AccessMiddleware

# Создаем роутер для обработчиков бармена
barmen_router = Router()
barmen_router.message.middleware(AccessMiddleware(allowed_user_ids=ACCESS_IDS))


class BarmenInitialStates(StatesGroup):
    INITIAL_STATE = State()
    WAITING_CHOOSE_INITIAL_ACTION = State()
    SHIPMENT_INITIAL_STATE = State()


# Применяем миддлварь проверки роли
barmen_router.message.filter(IsShipmentsRole())


STATES_BY_TEXT = {
    INITIAL_BUTTONS[-1]: BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND
}

#
# async def set_state(event: types.Message, state: FSMContext, new_state: State):
#     state_meta = {
#         BarmenInitialStates.INITIAL_STATE: {},
#         BarmenInitialStates.WAITING_CHOOSE_INITIAL_ACTION: {"pre_message": "Выберите действие",
#                                                             "pre_keyboard": get_initial_keyboard()},
#         BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND: {"pre_message": "Введите часть названия продукта:"}
#     }
#     state_dict = state_meta.get(new_state, {})
#     pre_message = state_dict.get("pre_message")
#     response_keyboard = state_dict.get("pre_keyboard")
#     await state.set_state(new_state)
#     if response_keyboard:
#         await event.answer(pre_message, response_keyboard=response_keyboard)
#     else:
#         await event.answer(pre_message)



@barmen_router.message(StateFilter(BarmenInitialStates.INITIAL_STATE, None))
async def barmen_back(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(BarmenInitialStates.WAITING_CHOOSE_INITIAL_ACTION)
    keyboard = get_initial_keyboard()
    await message.answer("Выберите действие", reply_markup=keyboard)


@barmen_router.message(StateFilter(BarmenInitialStates.INITIAL_STATE, None))
async def barmen_back2(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(BarmenInitialStates.WAITING_CHOOSE_INITIAL_ACTION)
    keyboard = get_initial_keyboard()
    await message.answer("Выберите действие", reply_markup=keyboard)


@barmen_router.message(BarmenInitialStates.WAITING_CHOOSE_INITIAL_ACTION)
async def choose_action(message: types.Message, state: FSMContext):
    new_state = STATES_BY_TEXT.get(message.text)

    if new_state:
        await state.set_state(new_state)
    else:
        await state.set_state(BarmenInitialStates.INITIAL_STATE)
        await message.answer("Выберите из предложенных действий")


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
    data = await state.get_data()
    categories_sequence = data.get("categories_sequence", [])
    if len(categories_sequence) == 0:
        await state.reset_state()
        await BarmenInitialStates.INITIAL_STATE.set()
        await message.answer("Выберите действие", reply_markup=get_initial_keyboard())
        return

    await ReceivingStates.WAITING_CATEGORY_NAME.set()
    categories_sequence = categories_sequence[:-1]
    await state.update_data(categories_sequence=categories_sequence)
    categories = product_storage.get_product_categories(categories_sequence)
    if categories:
        keyboard = create_range_keyboard(f"0-{PRODUCTS_RANGE}", categories)
        # keyboard.add(KeyboardButton(text="Назад"))
        await message.answer("Выберите", reply_markup=keyboard)
    else:
        await BarmenInitialStates.INITIAL_STATE.set()
        await message.answer("Выберите действие", reply_markup=get_initial_keyboard())


PRODUCTS_RANGE = 3


class ReceivingStates(StatesGroup):
    WAITING_SUPPLY_NAME = State()
    WAITING_SUPPLY_QUANTITY = State()
    WAITING_CATEGORY_NAME = State()


def create_range_keyboard(products_range: str, names: List[str]) -> ReplyKeyboardMarkup:
    keyboard = get_keyboard(names)
    texts = ["Показать поставку", "Назад", "В начало"]
    buttons = [KeyboardButton(text=text) for text in texts]
    keyboard.add(*buttons)
    return keyboard
