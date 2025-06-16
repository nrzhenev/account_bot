import re
from typing import List, Optional

from aiogram import types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup

import product_storage
from domain.product import ProductVolume
from pkg import get_most_similar_strings, get_keyboard
from src.handlers.barmen.initial_handlers import (_increments_string, BarmenInitialStates,
                                                  barmen_router, barmen_mh, barmen_event, BACK_BUTTON, RETURN_BUTTON)
from src.handlers.roles import IsShipmentsRole
from src.handlers.state_messages import StateWithData
from src.poster_api.ingredients import send_shipment as shipment_to_poster, Supply


class WriteOffStates(StatesGroup):
    WAITING_SUPPLY_NAME = StateWithData()
    WAITING_SUPPLY_QUANTITY = StateWithData("Или можете нажать назад", get_keyboard([BACK_BUTTON]))
    WAITING_CATEGORY_NAME = StateWithData()
    SHIPMENT_PRODUCT_ADDED = StateWithData("Показать списание или добавить еще продукт?",
                                           get_keyboard(["Показать списание", "Добавить еще"]))
    READY_TO_SEND = StateWithData("Отправить или добавить еще?")
    SEND_SHIPMENT = StateWithData()

barmen_mh.add_transition(BarmenInitialStates.WRITE_OFF_PRODUCTS, WriteOffStates.WAITING_SUPPLY_NAME)

barmen_mh.add_transition(WriteOffStates.WAITING_SUPPLY_NAME, BarmenInitialStates.WRITE_OFF_PRODUCTS, BACK_BUTTON)
barmen_mh.add_transition(WriteOffStates.WAITING_SUPPLY_NAME, WriteOffStates.WAITING_SUPPLY_QUANTITY)
barmen_mh.add_transition(WriteOffStates.WAITING_SUPPLY_NAME, BarmenInitialStates.WRITE_OFF_PRODUCTS, RETURN_BUTTON)
barmen_mh.add_transition(WriteOffStates.WAITING_SUPPLY_NAME, BarmenInitialStates.WAITING_CHOOSE_ACTION)

barmen_mh.add_transition(WriteOffStates.WAITING_SUPPLY_QUANTITY, BarmenInitialStates.WRITE_OFF_PRODUCTS, BACK_BUTTON)
barmen_mh.add_transition(WriteOffStates.WAITING_SUPPLY_QUANTITY, WriteOffStates.SHIPMENT_PRODUCT_ADDED)

barmen_mh.add_transition(WriteOffStates.SHIPMENT_PRODUCT_ADDED, BarmenInitialStates.WRITE_OFF_PRODUCTS, "Добавить еще")
barmen_mh.add_transition(WriteOffStates.SHIPMENT_PRODUCT_ADDED, WriteOffStates.READY_TO_SEND, "Показать списание")

barmen_mh.add_transition(WriteOffStates.READY_TO_SEND, WriteOffStates.SEND_SHIPMENT, "Отправить списание")
barmen_mh.add_transition(WriteOffStates.READY_TO_SEND, BarmenInitialStates.WRITE_OFF_PRODUCTS, "Добавить еще")

barmen_mh.add_transition(WriteOffStates.SEND_SHIPMENT, BarmenInitialStates.WAITING_CHOOSE_ACTION)


@barmen_router.message(BarmenInitialStates.WRITE_OFF_PRODUCTS)
@barmen_event
async def suggest_products(message: types.Message, state: FSMContext):
    await message.answer("Выберите",
                         reply_markup=get_keyboard([BACK_BUTTON, RETURN_BUTTON] + get_products_names_most_similar(message.text)))


@barmen_router.message(WriteOffStates.WAITING_SUPPLY_NAME)
@barmen_event
async def choose_products(message: types.Message, state: FSMContext):
    product = product_storage.get_product_by_name(message.text)
    await state.update_data({"current_product": product})
    await message.answer(f"Для {product.name} введите количество {product.unit}")


@barmen_router.message(IsShipmentsRole(),
                       StateFilter(WriteOffStates.WAITING_SUPPLY_QUANTITY))
@barmen_event
async def chose_quantity(message: types.Message, state: FSMContext):
    quantity = re.match(r'^[+-]?\d+(\.\d+)?$', message.text)
    if not quantity:
        await message.answer("Введите число в формате 331.12 или 232")
        return -1

    data = await state.get_data()
    write_off_product_increments = data.get("write_off_product_increments", [])
    quantity = float(message.text)
    product = data['current_product']
    pi = ProductVolume(product.id, quantity)
    write_off_product_increments.append(pi)
    await state.update_data(write_off_product_increments=write_off_product_increments)
    await message.answer(f"Для {product.name} добавил в списание {quantity} {data['current_product'].unit}")


@barmen_router.message(IsShipmentsRole(), WriteOffStates.SHIPMENT_PRODUCT_ADDED)
@barmen_event
async def shipment_product_added(message: types.Message, state: FSMContext):
    if message.text == "Показать списание":
        await show_shipment(message, state)



async def show_shipment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    write_off_product_increments = data.get("write_off_product_increments", [])
    keyboard = get_keyboard(["Отправить списание", "Добавить еще"])
    answer = await _increments_string(write_off_product_increments)
    await message.answer(answer, reply_markup=keyboard)


@barmen_router.message(IsShipmentsRole(), WriteOffStates.READY_TO_SEND)
@barmen_event
async def ready_to_send(message: types.Message, state: FSMContext):
    if message.text == "Отправить списание":
        await send_shipment(message, state)


def send_shipment_to_poster(write_off_product_increments: List[ProductVolume]):
    supplies = []
    for increment in write_off_product_increments:
        product = product_storage.get_product_by_id(increment.product_id)
        supplies.append(Supply(product.poster_id, increment.quantity, product.price))
    shipment_to_poster(supplies)


@barmen_router.message(IsShipmentsRole(),
                       StateFilter(WriteOffStates.SEND_SHIPMENT))
@barmen_event
async def send_shipment(message: types.Message, state: FSMContext):
    #ps = poster_storage.PosterStorage()
    data = await state.get_data()
    write_off_product_increments = data.get("write_off_product_increments", [])
    if not write_off_product_increments:
        await message.answer("Списание пустое")
    else:
        #date = await get_now_date_async(state)
        #send_shipment_to_poster(write_off_product_increments)
        await state.update_data(write_off_product_increments=[])
        await message.answer("Списание отправлено")
#
#
# @barmen_router.message(IsShipmentsRole(), StateFilter(BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND))
# async def choose_product(message: types.Message, state: FSMContext):
#     if message.text in []:
#         pass
#     sub_name = message.text
#     product = product_storage.get_product_by_name(sub_name)
#     if product:
#         await state.set_state(WriteOffStates.WAITING_SUPPLY_QUANTITY)
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
