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
from typing import List

from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from handlers.fsm_graph import FSM


def get_initial_keyboard():
    buttons = INITIAL_BUTTONS
    return get_keyboard(buttons, True)


FSM_GRAPH = {
    PizzaOrderStates.choose_category: {
        "Пепперони": PizzaOrderStates.choose_size,
        "Маргарита": PizzaOrderStates.choose_size,
    },
    PizzaOrderStates.choose_size: {
        "Маленькая": PizzaOrderStates.choose_payment,
        "Большая": PizzaOrderStates.choose_payment,
    },
    PizzaOrderStates.choose_payment: {
        "Картой": None,
        "Наличными": None,
    },
}


INITIAL_BUTTONS = ["Ввести поставки от руки"]


async def reply_state_announcement_message(event: types.Message, state: str):
    state_dict = MetaStatesGroup.STATE_META[state]
    message = state_dict.get("message")
    keyboard = state_dict.get("keyboard")
    if message:
        if keyboard:
            await event.answer(message, reply_markup=keyboard)
        else:
            await event.answer(message)


class BarmenInitMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: types.Message, data: dict):
        result = await handler(event, data)

        state = data.get("state")
        current_state = await state.get_state()
        await reply_state_announcement_message(event, current_state)

        return result


# Создаем роутер для обработчиков бармена
barmen_router = Router()
barmen_router.message.middleware(AccessMiddleware(allowed_user_ids=ACCESS_IDS))
barmen_router.message.middleware(BarmenInitMiddleware())


class CustomState(State):
    def __init__(self,
                 initialization_response_message: str=None,
                 initialization_response_keyboard: ReplyKeyboardMarkup=None):
        self.message = initialization_response_message
        self.keyboard = initialization_response_keyboard
        super().__init__()


class MetaStatesGroup(StatesGroup):
    STATE_META: dict[str, dict] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        for name, value in cls.__dict__.items():
            if isinstance(value, CustomState):
                full_state_name = f"{cls.__name__}:{name}"
                cls.STATE_META[full_state_name] = {
                    "message": value.message,
                    "keyboard": value.keyboard
                }


    @classmethod
    def get_all_meta(cls):
        return cls.subclasses_meta


class BarmenInitialStates(MetaStatesGroup):
    INITIAL_STATE = State()
    WAITING_CHOOSE_INITIAL_ACTION = State()
    RECIEVE_SHIPMENT_BY_HAND = State()


# class BarmenInitialStates(MetaStatesGroup):
#     INITIAL_STATE = CustomState()
#     WAITING_CHOOSE_INITIAL_ACTION = CustomState("Выберите действие", get_initial_keyboard())
#     RECIEVE_SHIPMENT_BY_HAND = CustomState("Введите часть названия продукта:")


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


@barmen_router.message(StateFilter(BarmenInitialStates.INITIAL_STATE, None))
async def barmen_back2(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(BarmenInitialStates.WAITING_CHOOSE_INITIAL_ACTION)


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
