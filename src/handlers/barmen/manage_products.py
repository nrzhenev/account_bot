from typing import Optional

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup

import product_storage
from pkg import get_most_similar_strings, get_keyboard
from src.handlers.barmen.initial_handlers import (BarmenInitialStates,
                                                  barmen_router, barmen_mh, barmen_event, BACK_BUTTON, RETURN_BUTTON)
from domain.product import PosterProduct
from src.handlers.state_messages import StateWithData
from src.poster_api.poster_managing import products_containing_ingredient, turn_on_products, turn_off_products


class ManageProductsStates(StatesGroup):
    WAITING_SUPPLY_NAME = StateWithData()
    PRODUCTS_DECISION = StateWithData("выберите действие", get_keyboard(["Отключить", "Включить", BACK_BUTTON, RETURN_BUTTON]))


TURN_OFF = "Отключить"
TURN_ON = "Включить"


barmen_mh.add_transition(BarmenInitialStates.MANAGE_PRODUCTS, ManageProductsStates.WAITING_SUPPLY_NAME)
barmen_mh.add_transition(ManageProductsStates.WAITING_SUPPLY_NAME, ManageProductsStates.PRODUCTS_DECISION)
barmen_mh.add_transition(ManageProductsStates.PRODUCTS_DECISION, BarmenInitialStates.WAITING_CHOOSE_ACTION)
#barmen_mh.add_transition(ManageProductsStates.WAITING_SUPPLY_NAME, ManageProductsStates.PRODUCTS_DECISION, TURN_OFF)
#barmen_mh.add_transition(ManageProductsStates.WAITING_SUPPLY_NAME, ManageProductsStates.PRODUCTS_DECISION, TURN_ON)

barmen_mh.add_transition(ManageProductsStates.WAITING_SUPPLY_NAME, BarmenInitialStates.MANAGE_PRODUCTS, BACK_BUTTON)
barmen_mh.add_transition(ManageProductsStates.PRODUCTS_DECISION, BarmenInitialStates.MANAGE_PRODUCTS, BACK_BUTTON)

barmen_mh.add_transition(ManageProductsStates.WAITING_SUPPLY_NAME, BarmenInitialStates.WAITING_CHOOSE_ACTION, RETURN_BUTTON)
barmen_mh.add_transition(ManageProductsStates.PRODUCTS_DECISION, BarmenInitialStates.WAITING_CHOOSE_ACTION, RETURN_BUTTON)

@barmen_router.message(BarmenInitialStates.MANAGE_PRODUCTS)
@barmen_event
async def suggest_products_for_turn_of(message: types.Message, state: FSMContext):
    await message.answer("Выберите",
                         reply_markup=get_keyboard([BACK_BUTTON, RETURN_BUTTON] + get_products_names_most_similar(message.text)))


@barmen_router.message(ManageProductsStates.WAITING_SUPPLY_NAME)
@barmen_event
async def show_products(message: types.Message, state: FSMContext):
    ingredient = product_storage.get_product_by_name(message.text)
    target_products = products_containing_ingredient(ingredient.poster_id)
    products = []
    for tp in target_products:
        products.append(PosterProduct(int(tp["product_id"]), tp["product_name"], tp["category_name"]))
    names = [p.name for p in products]
    await state.update_data({"current_managing_products": products})

    names_string = '\n'.join(names)
    text = f"Для приведенных продуктов\n\n{names_string}"
    await message.answer(text)


@barmen_router.message(ManageProductsStates.PRODUCTS_DECISION)
@barmen_event
async def products_decision(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_products = data.get("current_managing_products")
    if not current_products:
        return

    if message.text == TURN_OFF:
        turn_off_products([product.poster_id for product in current_products])
        await message.answer(f"Отключили указанные продукты")
    elif message.text == TURN_ON:
        turn_on_products([product.poster_id for product in current_products])
        await message.answer(f"Включили указанные продукты")


def get_products_names_most_similar(name, num: Optional[int]=None):
    products = product_storage.get_products()
    names = [p.name for p in products]
    if not num:
        return get_most_similar_strings(name, names)
    return get_most_similar_strings(name, names)[:num]
