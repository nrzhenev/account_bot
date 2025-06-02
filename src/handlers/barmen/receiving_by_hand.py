import re

from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

import product_storage
from src.handlers.barmen.initial_handlers import get_initial_keyboard, _increments_string, _back_handler, BarmenInitialStates, barmen_router, MetaStatesGroup, CustomState
from src.handlers.roles import IsShipmentsRole
from src.handlers.state_messages import StateWithData
from pkg import get_now_date_async, ActionType, get_most_similar_strings
from domain.product import ProductVolume
from pkg import get_keyboard
from aiogram import types


class ReceivingByHandStates(MetaStatesGroup):
    RECIEVE_SHIPMENT_BY_HAND = CustomState()
    WAITING_SUPPLY_NAME = CustomState()
    WAITING_SUPPLY_QUANTITY = CustomState()
    WAITING_CATEGORY_NAME = CustomState()
    SHIPMENT_PRODUCT_ADDED = CustomState("Посмотреть поставку или добавить еще продукт?", get_keyboard(["Показать поставку", "Ввести поставки от руки"]))
    SHOW_SHIPMENT = CustomState()


# @barmen_router.message(BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND)
# async def choose_product(message: types.Message, state: FSMContext):
#     print("here")
#     await message.answer(f"Продукт:")
#     await state.set_state(ReceivingByHandStates.WAITING_SUPPLY_NAME)


@barmen_router.message(IsShipmentsRole(),
                       StateFilter(ReceivingByHandStates.WAITING_SUPPLY_QUANTITY))
async def chose_quantity(message: types.Message, state: FSMContext):
    if re.fullmatch("Назад", message.text):
        return await _back_handler(message, state)
    quantity = re.match(r'^[+-]?\d+(\.\d+)?$', message.text)
    if not quantity:
        await message.answer("Введите число в формате 331.12 или 232")
        return

    data = await state.get_data()
    product_increments = data.get("product_increments", [])
    quantity = float(message.text)
    product = data['current_product']
    pi = ProductVolume(product.id, quantity)
    product_increments.append(pi)
    await state.update_data(product_increments=product_increments)

    await message.answer(f"Для {product.name} добавил в поставку {quantity} {data['current_product'].measurement_unit}")
    await state.set_state(ReceivingByHandStates.SHIPMENT_PRODUCT_ADDED)


@barmen_router.message(IsShipmentsRole(), ReceivingByHandStates.SHIPMENT_PRODUCT_ADDED)
async def shipment_product_added(message: types.Message, state: FSMContext):
    pass


@barmen_router.message(IsShipmentsRole(),
                       StateFilter(ReceivingByHandStates.SHOW_SHIPMENT))
async def show_shipment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    product_increments = data.get("product_increments", [])
    if not product_increments:
        keyboard = get_keyboard(["Ввести поставки"])
        await message.answer("Поставка пуста", reply_markup=keyboard)
    else:
        keyboard = get_keyboard(["Отправить поставку", "Ввести поставки от руки"])
        answer = await _increments_string(product_increments)
        await message.answer(answer, reply_markup=keyboard)


@barmen_router.message(IsShipmentsRole(),
                       lambda message: message.text == "Отправить поставку",
                       StateFilter(ReceivingByHandStates.WAITING_SUPPLY_NAME))
async def send_shipment(message: types.Message, state: FSMContext):
    #ps = poster_storage.PosterStorage()
    data = await state.get_data()
    product_increments = data.get("product_increments", [])
    if not product_increments:
        keyboard = get_keyboard(["Ввести поставки"])
        await message.answer("Поставка пустая", reply_markup=keyboard)
    else:
        date = await get_now_date_async(state)
        product_storage.increment_products(product_increments,
                                           message.from_user.id,
                                           ActionType.RECEIVING,
                                           date)
        #await ps.increment_products(product_increments)
        await state.update_data(product_increments=[])
        keyboard = get_initial_keyboard()
        await state.set_state(BarmenInitialStates.INITIAL_STATE)
        await message.answer("Поставка отправлена", reply_markup=keyboard)


@barmen_router.message(IsShipmentsRole(), StateFilter(BarmenInitialStates.RECIEVE_SHIPMENT_BY_HAND))
async def choose_product(message: types.Message, state: FSMContext):
    if message.text in []:
        pass
    sub_name = message.text
    product = product_storage.get_product_by_name(sub_name)
    if product:
        await state.set_state(ReceivingByHandStates.WAITING_SUPPLY_QUANTITY)
        await message.answer(f"Для {product.name} введите количество {product.measurement_unit}:")
        await state.update_data(current_product=product)
        return

    names = get_products_names_most_similar(sub_name, 5)
    keyboard = get_keyboard(names + ["Назад"])
    await message.answer(f"Выберите из предложенных или повторите попытку", reply_markup=keyboard)


def get_products_names_most_similar(name, num: int):
    products = product_storage.get_products()
    names = [p.name for p in products]
    return get_most_similar_strings(name, names)[:num]
