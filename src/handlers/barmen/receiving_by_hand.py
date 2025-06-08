import re
from typing import List, Optional

from aiogram import types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup

import product_storage
from domain.product import ProductVolume
from pkg import get_now_date_async, ActionType, get_most_similar_strings, get_keyboard
from src.handlers.barmen.initial_handlers import (get_initial_keyboard, _increments_string, BarmenInitialStates,
                                                  barmen_router, barmen_mh, barmen_event, BACK_BUTTON)
from src.poster_api.ingredients import send_shipment as shipment_to_poster, Supply
from src.handlers.roles import IsShipmentsRole
from src.handlers.state_messages import StateWithData


class ReceivingByHandStates(StatesGroup):
    WAITING_SUPPLY_NAME = StateWithData()
    WAITING_SUPPLY_QUANTITY = StateWithData("Или можете нажать назад", get_keyboard([BACK_BUTTON]))
    WAITING_CATEGORY_NAME = StateWithData()
    SHIPMENT_PRODUCT_ADDED = StateWithData("Показать поставку или добавить еще продукт?",
                                           get_keyboard(["Показать поставку", "Добавить еще"]))
    READY_TO_SEND = StateWithData("Отправить или добавить еще?")
    SEND_SHIPMENT = StateWithData()

barmen_mh.add_transition(BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND, ReceivingByHandStates.WAITING_SUPPLY_NAME)

barmen_mh.add_transition(ReceivingByHandStates.WAITING_SUPPLY_NAME, BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND, BACK_BUTTON)
barmen_mh.add_transition(ReceivingByHandStates.WAITING_SUPPLY_NAME, ReceivingByHandStates.WAITING_SUPPLY_QUANTITY)

barmen_mh.add_transition(ReceivingByHandStates.WAITING_SUPPLY_QUANTITY, BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND, BACK_BUTTON)
barmen_mh.add_transition(ReceivingByHandStates.WAITING_SUPPLY_QUANTITY, ReceivingByHandStates.SHIPMENT_PRODUCT_ADDED)

barmen_mh.add_transition(ReceivingByHandStates.SHIPMENT_PRODUCT_ADDED, BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND, "Добавить еще")
barmen_mh.add_transition(ReceivingByHandStates.SHIPMENT_PRODUCT_ADDED, ReceivingByHandStates.READY_TO_SEND, "Показать поставку")

barmen_mh.add_transition(ReceivingByHandStates.READY_TO_SEND, ReceivingByHandStates.SEND_SHIPMENT, "Отправить поставку")
barmen_mh.add_transition(ReceivingByHandStates.READY_TO_SEND, BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND, "Добавить еще")

barmen_mh.add_transition(ReceivingByHandStates.SEND_SHIPMENT, BarmenInitialStates.WAITING_CHOOSE_ACTION)


@barmen_router.message(BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND)
@barmen_event
async def suggest_products(message: types.Message, state: FSMContext):
    await message.answer("Выберите",
                         reply_markup=get_keyboard([BACK_BUTTON] + get_products_names_most_similar(message.text)))


@barmen_router.message(ReceivingByHandStates.WAITING_SUPPLY_NAME)
@barmen_event
async def choose_products(message: types.Message, state: FSMContext):
    product = product_storage.get_product_by_name(message.text)
    await state.update_data({"current_product": product})
    await message.answer(f"Для {product.name} введите количество {product.unit}")


@barmen_router.message(IsShipmentsRole(),
                       StateFilter(ReceivingByHandStates.WAITING_SUPPLY_QUANTITY))
@barmen_event
async def chose_quantity(message: types.Message, state: FSMContext):
    quantity = re.match(r'^[+-]?\d+(\.\d+)?$', message.text)
    if not quantity:
        await message.answer("Введите число в формате 331.12 или 232")
        return -1

    data = await state.get_data()
    product_increments = data.get("product_increments", [])
    quantity = float(message.text)
    product = data['current_product']
    pi = ProductVolume(product.id, quantity)
    product_increments.append(pi)
    await state.update_data(product_increments=product_increments)
    await message.answer(f"Для {product.name} добавил в поставку {quantity} {data['current_product'].unit}")


@barmen_router.message(IsShipmentsRole(), ReceivingByHandStates.SHIPMENT_PRODUCT_ADDED)
@barmen_event
async def shipment_product_added(message: types.Message, state: FSMContext):
    if message.text == "Показать поставку":
        await show_shipment(message, state)



async def show_shipment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    product_increments = data.get("product_increments", [])
    if not product_increments:
        keyboard = get_keyboard(["Ввести поставки"])
        await message.answer("Поставка пуста", reply_markup=keyboard)
    else:
        keyboard = get_keyboard(["Отправить поставку", "Добавить еще"])
        answer = await _increments_string(product_increments)
        await message.answer(answer, reply_markup=keyboard)


@barmen_router.message(IsShipmentsRole(), ReceivingByHandStates.READY_TO_SEND)
@barmen_event
async def ready_to_send(message: types.Message, state: FSMContext):
    if message.text == "Отправить поставку":
        await send_shipment(message, state)


def send_shipment_to_poster(product_increments: List[ProductVolume]):
    supplies = []
    for increment in product_increments:
        product = product_storage.get_product_by_id(increment.product_id)
        supplies.append(Supply(product.poster_id, increment.quantity, product.price))
    shipment_to_poster(supplies)


@barmen_router.message(IsShipmentsRole(),
                       StateFilter(ReceivingByHandStates.SEND_SHIPMENT))
@barmen_event
async def send_shipment(message: types.Message, state: FSMContext):
    #ps = poster_storage.PosterStorage()
    data = await state.get_data()
    product_increments = data.get("product_increments", [])
    if not product_increments:
        await message.answer("Поставка пустая")
    else:
        #date = await get_now_date_async(state)
        #send_shipment_to_poster(product_increments)
        await state.update_data(product_increments=[])
        await message.answer("Поставка отправлена")
#
#
# @barmen_router.message(IsShipmentsRole(), StateFilter(BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND))
# async def choose_product(message: types.Message, state: FSMContext):
#     if message.text in []:
#         pass
#     sub_name = message.text
#     product = product_storage.get_product_by_name(sub_name)
#     if product:
#         await state.set_state(ReceivingByHandStates.WAITING_SUPPLY_QUANTITY)
#         await message.answer(f"Для {product.name} введите количество {product.unit}:")
#         await state.update_data(current_product=product)
#         return
#
#     names = get_products_names_most_similar(sub_name, 5)
#     keyboard = get_keyboard(names + [BACK_BUTTON])
#     await message.answer(f"Выберите из предложенных или повторите попытку", reply_markup=keyboard)


def get_products_names_most_similar(name, num: Optional[int]=None):
    products = product_storage.get_products()
    names = [p.name for p in products]
    if not num:
        return get_most_similar_strings(name, names)
    return get_most_similar_strings(name, names)[:num]
