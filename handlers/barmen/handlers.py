import re
from typing import List, Optional

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

import money
import product_storage
from product_storage import ProductVolume
#import poster_storage
#from poster_storage import PosterStorage, ProductVolume, Product
from pkg import dp, get_dates_from_string, get_most_similar_strings, get_keyboard, verify_message_is_value, ActionType, get_now_date_async
from handlers.roles import IsShipmentsRole, IsAdmin


PRODUCTS_RANGE = 3
MONEY_RECEPIENTS = ["Мириан", "Никита", "Другое"]
OTHER_PURPOSES_FOR_MONEY_OUT = ["Зарплата", "Самостоятельная докупка продуктов", "Другие траты"]


class BarmenStates(StatesGroup):
    INITIAL_STATE = State()


class ReceivingByHandStates(StatesGroup):
    WAITING_SUPPLY_NAME = State()
    WAITING_SUPPLY_QUANTITY = State()
    WAITING_CATEGORY_NAME = State()


class MoneyReceivingStates(StatesGroup):
    WAITING_FOR_MONEY_AMOUNT_IN = State()


class MoneyTransferStates(StatesGroup):
    WAITING_TO_CHOOSE_MONEY_RECEPIENT = State()
    WAITING_TO_GET_MONEY_OUT_PURPOSE = State()
    WAITING_FOR_COMMENTS_ON_PURPOSE = State()
    WAITING_FOR_MONEY_AMOUNT_OUT = State()


class ReceivingStates(StatesGroup):
    WAITING_SUPPLY_NAME = State()
    WAITING_SUPPLY_QUANTITY = State()
    WAITING_CATEGORY_NAME = State()


def get_initial_keyboard():
    buttons = ["Ввести поставки", "Пополнение наличных", "Выдача наличных", "Ввести поставки от руки"]
    return get_keyboard(buttons)


# @dp.message_handler(IsShipmentsRole(), state=BarmenStates.INITIAL_STATE)
# async def barmen_start(message: types.Message, state: FSMContext):
#     await state.reset_state()
#     keyboard = get_initial_keyboard()
#     await message.answer("Выберите действие", reply_markup=keyboard)


@dp.message_handler(IsShipmentsRole(), commands=["cd"], state="*")
async def change_date(message: types.Message, state: FSMContext):
    try:
        arg = message.text.split()[1]
        d = re.findall("\d", arg)
        if len(d) == 8:
            arg = f"{d[0]+d[1]}-{d[2]+d[3]}-{''.join(d[4:])}"
        elif len(d) == 6:
            arg = f"{d[0]+d[1]}-{d[2]+d[3]}-20{''.join(d[4:])}"
        elif len(d) == 4:
            arg = f"{d[0] + d[1]}-{d[2] + d[3]}-2024"
        date = get_dates_from_string(arg)[0]
    except:
        return
    await state.update_data(date=date.date())
    await message.answer(f"Поменял дату на {date.strftime('%d-%m-%y')}")


@dp.message_handler(IsShipmentsRole(), state=None)
async def barmen_start(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=False)
    await BarmenStates.INITIAL_STATE.set()
    keyboard = get_initial_keyboard()
    await message.answer("Выберите действие", reply_markup=keyboard)


@dp.message_handler(IsShipmentsRole(), commands=["start"], state="*")
async def barmen_start_2(message: types.Message, state: FSMContext):
    await state.reset_state()
    await BarmenStates.INITIAL_STATE.set()
    keyboard = get_initial_keyboard()
    await message.answer("Выберите действие", reply_markup=keyboard)


@dp.message_handler(IsShipmentsRole(), commands=["s"], state="*")
async def barmen_start_2(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=False)
    await BarmenStates.INITIAL_STATE.set()
    keyboard = get_initial_keyboard()
    await message.answer("Выберите действие", reply_markup=keyboard)


@dp.message_handler(IsShipmentsRole(), lambda message: message.text=="Назад",
                    state=ReceivingByHandStates.WAITING_SUPPLY_NAME)
async def barmen_start2(message: types.Message, state: FSMContext):
    await state.reset_state()
    await BarmenStates.INITIAL_STATE.set()
    keyboard = get_initial_keyboard()
    await message.answer("Выберите действие", reply_markup=keyboard)



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


# @dp.message_handler(IsShipmentsRole())
# async def handle_message(message: types.Message):
#     try:
#         save_message(data_base, message)
#
#         answer_message = (
#             f"Поздравляю, вы бармен!")
#     except exceptions.NotCorrectMessage as e:
#         await message.answer(str(e))
#         return
#     # answer_message = (
#     #     f"Добавлены траты {expense.amount} руб на {expense.category_name}.\n\n"
#     #     f"{expenses.get_today_statistics()}")
#     await message.answer(answer_message)


def create_range_keyboard(products_range: str, names: List[str]) -> ReplyKeyboardMarkup:
    keyboard = get_keyboard(names)
    texts = ["Показать поставку", "Назад", "В начало"]
    buttons = [KeyboardButton(text=text) for text in texts]
    keyboard.add(*buttons)
    return keyboard


# Пополнение наличных



@dp.message_handler(IsShipmentsRole(), lambda message: message.text == "Пополнение наличных", state="*")
async def products_categories(message: types.Message, state: FSMContext):
    await MoneyReceivingStates.WAITING_FOR_MONEY_AMOUNT_IN.set()
    await message.answer("Введите сумму", reply_markup=ReplyKeyboardRemove())


@dp.message_handler(IsShipmentsRole(), state=MoneyReceivingStates.WAITING_FOR_MONEY_AMOUNT_IN)
async def products_categories(message: types.Message, state: FSMContext):
    if not await verify_message_is_value(message):
        return

    initial_money = money.get_balance("Касса")
    inc = float(re.search("\d+[,.]?\d*", message.text).group())
    money.increment("Касса", inc)
    sum = initial_money + inc
    keyboard = get_initial_keyboard()
    await BarmenStates.INITIAL_STATE.set()
    await message.answer(f"Добавили {inc} в кассу.\nИтого {sum}", reply_markup=keyboard)


# Выдача наличных


@dp.message_handler(IsShipmentsRole(), lambda message: message.text == "Выдача наличных", state="*")
async def money_out(message: types.Message, state: FSMContext):
    buttons = MONEY_RECEPIENTS
    keyboard = get_keyboard(buttons)
    await MoneyTransferStates.WAITING_TO_CHOOSE_MONEY_RECEPIENT.set()
    await message.answer(f"Кому выдать деньги", reply_markup=keyboard)


@dp.message_handler(IsShipmentsRole(),
                    lambda message: message.text in OTHER_PURPOSES_FOR_MONEY_OUT,
                    state=MoneyTransferStates.WAITING_TO_GET_MONEY_OUT_PURPOSE)
async def money_out_other_purpose(message: types.Message, state: FSMContext):
    await message.answer(f"Добавьте комментарий")
    await MoneyTransferStates.WAITING_FOR_COMMENTS_ON_PURPOSE.set()


@dp.message_handler(IsShipmentsRole(),
                    state=MoneyTransferStates.WAITING_FOR_COMMENTS_ON_PURPOSE)
async def money_out_other_purpose(message: types.Message, state: FSMContext):
    await message.answer(f"Введите сумму")
    await MoneyTransferStates.WAITING_FOR_MONEY_AMOUNT_OUT.set()


@dp.message_handler(IsShipmentsRole(), state=MoneyTransferStates.WAITING_FOR_MONEY_AMOUNT_OUT)
async def money_out_amount(message: types.Message, state: FSMContext):
    if not await verify_message_is_value(message):
        return

    data = await state.get_data()
    recepient = data.get("money_out_recepient")
    if recepient:
        initial_money = money.get_balance("Касса")
        inc = float(re.search("\d+[,.]?\d*", message.text).group())
        #money.increment("Касса", inc * -1)
        sum = initial_money - inc
        money.transfer(inc, "Касса", recepient, message.from_user.id)
        keyboard = get_initial_keyboard()
        await BarmenStates.INITIAL_STATE.set()
        await message.answer(f"Выдали {inc} из кассы для {recepient}.\nОстаток в кассе {sum}", reply_markup=keyboard)
    else:
        initial_money = money.get_balance("Касса")
        inc = float(re.search("\d+[,.]?\d*", message.text).group())
        # if inc > 99:
        #     keyboard = get_initial_keyboard()
        #     await message.answer("А ты не офигел ли, пёс?", reply_markup=keyboard)
        #     await BarmenStates.INITIAL_STATE.set()
        #     return
        money.increment("Касса", inc*-1)
        sum = initial_money - inc
        keyboard = get_initial_keyboard()
        await BarmenStates.INITIAL_STATE.set()
        await message.answer(f"Выдали {inc} из кассы.\nОстаток в кассе {sum}", reply_markup=keyboard)


@dp.message_handler(IsShipmentsRole(),
                    lambda message: message.text in MONEY_RECEPIENTS,
                    state=MoneyTransferStates.WAITING_TO_CHOOSE_MONEY_RECEPIENT)
async def money_out_chose_recepient(message: types.Message, state: FSMContext):
    await state.update_data(money_out_recepient=None)
    if message.text == MONEY_RECEPIENTS[-1]:
        keyboard = get_keyboard(OTHER_PURPOSES_FOR_MONEY_OUT)
        await MoneyTransferStates.WAITING_TO_GET_MONEY_OUT_PURPOSE.set()
        await message.answer(f"Пожалуйста выберите цель", reply_markup=keyboard)
    else:
        recepient = message.text
        await state.update_data(money_out_recepient=recepient)
        await MoneyTransferStates.WAITING_FOR_MONEY_AMOUNT_OUT.set()
        await message.answer(f"Сколько вы хотите выдать {recepient}")


@dp.message_handler(IsShipmentsRole(), lambda message: message.text in ["Ввести поставки", "Категории"], state="*")
async def products_categories(message: types.Message, state: FSMContext):
    #ps = poster_storage.PosterStorage()
    #await ps.async_init()
    data = await state.get_data()
    categories_sequence = data.get("categories_sequence", [])
    categories = product_storage.get_product_categories(categories_sequence)
    keyboard = get_keyboard(categories)
    #keyboard.add(KeyboardButton(text="В начало"))
    keyboard.add(KeyboardButton(text="Назад"))
    await ReceivingStates.WAITING_CATEGORY_NAME.set()
    await message.answer("Выберите категорию", reply_markup=keyboard)


async def _back_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    categories_sequence = data.get("categories_sequence", [])
    if len(categories_sequence) == 0:
        await state.reset_state()
        await BarmenStates.INITIAL_STATE.set()
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
        await BarmenStates.INITIAL_STATE.set()
        await message.answer("Выберите действие", reply_markup=get_initial_keyboard())


@dp.message_handler(IsShipmentsRole(),
                    lambda message: message.text == "Назад",
                    state=ReceivingStates.WAITING_CATEGORY_NAME)
async def back_handler(message: types.Message, state: FSMContext):
    return await _back_handler(message, state)


@dp.message_handler(IsShipmentsRole(), lambda message: message.text == "Показать поставку", state=ReceivingStates.WAITING_CATEGORY_NAME)
async def show_shipment(message: types.Message, state: FSMContext):
    #ps = poster_storage.PosterStorage()
    data = await state.get_data()
    product_increments = data.get("product_increments", [])
    if not product_increments:
        keyboard = get_keyboard(["Ввести поставки"])
        # await ps.async_init()
        # await ReceivingStates.WAITING_SUPPLY_NAME.set()
        await message.answer("Поставка пуста", reply_markup=keyboard)
    else:
        keyboard = get_keyboard(["Отправить поставку", "Ввести поставки"])
        answer = await _increments_string(product_increments)
        await message.answer(answer, reply_markup=keyboard)
    #await ps.async_init()
    #await ReceivingStates.WAITING_SUPPLY_NAME.set()


@dp.message_handler(IsShipmentsRole(), lambda message: message.text == "Отправить поставку", state=ReceivingStates.WAITING_CATEGORY_NAME)
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
        await BarmenStates.INITIAL_STATE.set()
        await message.answer("Поставка отправлена", reply_markup=keyboard)


@dp.message_handler(IsShipmentsRole(), state=ReceivingStates.WAITING_CATEGORY_NAME)
async def choose_product(message: types.Message, state: FSMContext):
    products_category = message.text
    data = await state.get_data()
    categories_sequence = data.get("categories_sequence", [])
    categories_sequence.append(products_category)
    categories = product_storage.get_product_categories(categories_sequence)
    if categories:
        await state.update_data(categories_sequence=categories_sequence)
        keyboard = create_range_keyboard(f"0-{PRODUCTS_RANGE}", categories)
        #keyboard.add(KeyboardButton(text="Назад"))
        await message.answer("Выберите", reply_markup=keyboard)
        return
    product_name = message.text
    #ps = poster_storage.PosterStorage()
    #await ps.async_init()
    product = product_storage.get_product_by_name(product_name)
    await state.update_data(current_product=product,
                            product_name=product.name)
    keyboard = get_keyboard(["Назад"])
    await message.answer(f"Для {product.name} введите количество {product.measurement_unit}:", reply_markup=keyboard)
    await ReceivingStates.WAITING_SUPPLY_QUANTITY.set()


@dp.message_handler(IsShipmentsRole(), lambda message: message.text == "В начало", state="*")
async def send_shipment(message: types.Message, state: FSMContext):
    keyboard = get_initial_keyboard()
    await state.reset_state()
    await BarmenStates.INITIAL_STATE.set()
    await message.answer("Выберите действие", reply_markup=keyboard)


@dp.message_handler(IsShipmentsRole(),
                    state=ReceivingStates.WAITING_SUPPLY_QUANTITY)
async def chose_quantity(message: types.Message, state: FSMContext):
    if re.fullmatch("Назад", message.text):
        return await _back_handler(message, state)
    quantity = re.match(r'^[+-]?\d+(\.\d+)?$', message.text)
    if not quantity:
        await message.answer("Введите число в формате 331.12 или 232")
        return
    #ps = poster_storage.PosterStorage()

    data = await state.get_data()
    product_increments = data.get("product_increments", [])
    quantity = float(message.text)
    products_range = data.get("current_products_range") if data.get("current_products_range") else f"0-{PRODUCTS_RANGE}"
    categories_sequence = data.get("categories_sequence", [])
    categories = product_storage.get_product_categories(categories_sequence)
    keyboard = create_range_keyboard(products_range, categories)
    product_name = data['current_product'].name
    product = product_storage.get_product_by_name(product_name)
    #product = await ps.product_by_name(name)
    pi = ProductVolume(product.id, quantity)
    #pi = poster_storage.ProductVolume(product.id, quantity)
    product_increments.append(pi)
    await state.update_data(product_increments=product_increments)
    #await ps.increment_products([poster_storage.ProductVolume(product.id, quantity)])
    #product_storage.increment(name, quantity)
    await message.answer(f"Для {product_name} добавил в поставку {quantity} {data['current_product'].measurement_unit}",
                         reply_markup=keyboard)
    await ReceivingStates.WAITING_CATEGORY_NAME.set()


# @dp.message_handler(IsShipmentsRole(), lambda message: message.text == "Ввести поставки")
# async def products(message: types.Message, state: FSMContext):
#     await state.update_data(product_increments=[])
#     #ps = poster_storage.PosterStorage()
#     #await ps.async_init()
#     await ReceivingStates.WAITING_SUPPLY_NAME.set()
#     keyboard = await get_products_keyboard(f"0-{PRODUCTS_RANGE}")
#     await message.answer("Выберите продукт", reply_markup=keyboard)

#
# @dp.message_handler(IsShipmentsRole(), commands=["sh"])
# async def shipment(message: types.Message, state: FSMContext):
#     try:
#         save_message(data_base, message)
#         text = message.text.strip(" ,.")
#         if re.match("\d.+", text):
#             increments = product_storage.increments_from_text(text)
#             absent_products_increments = []
#             added_products_increments = []
#             for inc in increments:
#                 product = product_storage.get_product_by_name(inc.name)
#                 if not product:
#                     absent_products_increments.append(inc)
#                     continue
#                 added_products_increments.append(inc)
#                 product_storage.increment(inc.name, inc.quantity)
#             added_response = "\n".join([inc.name for inc in added_products_increments])
#             not_added_response = "\n".join([inc.name for inc in absent_products_increments])
#             await message.answer(f"Добавили поставки для {added_response}")
#             await message.answer(f"Не добавили: {not_added_response}")
#             return
#         elif re.match("[^\d\s]+", text):
#             names = get_products_names_most_similar(text, 5)
#             keyboard = get_keyboard(names)
#             await message.answer(f"Д", reply_markup=keyboard)
#         else:
#             raise ValueError("Неверный формат")
#         return
#     except exceptions.NotCorrectMessage as e:
#         await message.answer(str(e))
#         return


# @dp.message_handler(IsShipmentsRole(), state=ReceivingStates.WAITING_FOR_SUPPLY_ENTER_WITH_HINTS)
# async def shipment(message: types.Message, state: FSMContext):
#     try:
#         save_message(data_base, message)
#         await message.answer(f"Введите поставки в формате 100 яйца 2 нори")
#         await ReceivingStates.WAITING_FOR_FIRST_RESPONSE.set()
#         return
#     except exceptions.NotCorrectMessage as e:
#         await message.answer(str(e))
#         return

#
# @dp.message_handler(IsShipmentsRole(), state=ReceivingStates.WAITING_FOR_FIRST_RESPONSE)
# async def shipment_1(message: types.Message, state: FSMContext):
#     try:
#         data = await state.get_data()
#         product_increments = data["product_increments"]
#
#         save_message(data_base, message)
#         increments = product_storage.increments_from_text(message.text)
#         absent_products_increments = []
#         added_products_increments = []
#         for inc in increments:
#             product = product_storage.get_product_by_name(inc.name)
#             if not product:
#                 absent_products_increments.append(inc)
#                 continue
#             added_products_increments.append(inc)
#             #product_storage.increment(inc.name, inc.quantity)
#         product_increments += added_products_increments
#
#         added_response = "\n".join([inc.name for inc in added_products_increments])
#         not_added_response = "\n".join([inc.name for inc in absent_products_increments])
#         await message.answer(f"Добавили поставки для {added_response}")
#         #await message.answer(f"Не добавили: {not_added_response}")
#         #await state.update_data(previous_message=message.text)
#         #await ReceivingStates.WAITING_FOR_SECOND_RESPONSE.set()
#         return
#     except exceptions.NotCorrectMessage as e:
#         await message.answer(str(e))
#         return

#
# @dp.message_handler(IsShipmentsRole(), state=ReceivingStates.WAITING_FOR_SECOND_RESPONSE)
# async def shipment_2(message: types.Message, state: FSMContext):
#     try:
#         save_message(data_base, message)
#         data = await state.get_data()
#         previous_message_text = data["previous_message"]
#
#
#         #await ReceivingStates.WAITING_FOR_SECOND_RESPONSE.set()
#         return
#     except exceptions.NotCorrectMessage as e:
#         await message.answer(str(e))
#         return


# Receiving by hand


def get_products_names_most_similar(name, num: int):
    products = product_storage.get_products()
    names = [p.name for p in products]
    return get_most_similar_strings(name, names)[:num]


@dp.message_handler(IsShipmentsRole(),
                    lambda message: message.text == "Ввести поставки от руки",
                    state="*")
async def choose_product(message: types.Message, state: FSMContext):
    await message.answer(f"Продукт:")
    await ReceivingByHandStates.WAITING_SUPPLY_NAME.set()


async def _get_most_similar(message: types.Message, state: FSMContext):
    if message.text in []:
        pass
    sub_name = message.text
    product = product_storage.get_product_by_name(sub_name)
    if product:
        await ReceivingByHandStates.WAITING_SUPPLY_QUANTITY.set()
        await message.answer(f"Для {product.name} введите количество {product.measurement_unit}:")
        await state.update_data(current_product=product)
        return

    names = get_products_names_most_similar(sub_name, 5)
    keyboard = get_keyboard(names)
    keyboard.add(KeyboardButton(text="Назад"))
    await message.answer(f"Выберите из предложенных или повторите попытку", reply_markup=keyboard)


@dp.message_handler(IsShipmentsRole(),
                    state=ReceivingByHandStates.WAITING_SUPPLY_QUANTITY)
async def chose_quantity(message: types.Message, state: FSMContext):
    if re.fullmatch("Назад", message.text):
        return await _back_handler(message, state)
    quantity = re.match(r'^[+-]?\d+(\.\d+)?$', message.text)
    if not quantity:
        await message.answer("Введите число в формате 331.12 или 232")
        return
    #ps = poster_storage.PosterStorage()

    data = await state.get_data()
    product_increments = data.get("product_increments", [])
    quantity = float(message.text)
    categories_sequence = data.get("categories_sequence", [])
    product = data['current_product']
    #product = product_storage.get_product_by_name(product_name)
    pi = ProductVolume(product.id, quantity)
    #pi = poster_storage.ProductVolume(product.id, quantity)
    product_increments.append(pi)
    await state.update_data(product_increments=product_increments)
    #await ps.increment_products([poster_storage.ProductVolume(product.id, quantity)])
    #product_storage.increment(name, quantity)
    keyboard = get_keyboard(["Показать поставку", "Ввести поставки от руки"])
    await message.answer(f"Для {product.name} добавил в поставку {quantity} {data['current_product'].measurement_unit}", reply_markup=keyboard)
    await ReceivingByHandStates.WAITING_SUPPLY_NAME.set()


@dp.message_handler(IsShipmentsRole(), lambda message: message.text == "Показать поставку",
                    state=ReceivingByHandStates.WAITING_SUPPLY_NAME)
async def show_shipment(message: types.Message, state: FSMContext):
    #ps = poster_storage.PosterStorage()
    data = await state.get_data()
    product_increments = data.get("product_increments", [])
    if not product_increments:
        keyboard = get_keyboard(["Ввести поставки"])
        # await ps.async_init()
        # await ReceivingStates.WAITING_SUPPLY_NAME.set()
        await message.answer("Поставка пуста", reply_markup=keyboard)
    else:
        keyboard = get_keyboard(["Отправить поставку", "Ввести поставки от руки"])
        answer = await _increments_string(product_increments)
        await message.answer(answer, reply_markup=keyboard)
    #await ps.async_init()
    #await ReceivingStates.WAITING_SUPPLY_NAME.set()


@dp.message_handler(IsShipmentsRole(),
                    lambda message: message.text == "Отправить поставку",
                    state=ReceivingByHandStates.WAITING_SUPPLY_NAME)
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
        await BarmenStates.INITIAL_STATE.set()
        await message.answer("Поставка отправлена", reply_markup=keyboard)


@dp.message_handler(IsShipmentsRole(), state=ReceivingByHandStates.WAITING_SUPPLY_NAME)
async def choose_product(message: types.Message, state: FSMContext):
    return await _get_most_similar(message, state)
