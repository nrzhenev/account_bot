import re
from typing import List, Optional

import asyncio
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
import aiogram

import exceptions
import money
import product_storage
from product_storage import ProductVolume
import expenses as expenses_module
#import poster_storage
#from poster_storage import PosterStorage, ProductVolume, Product
from pkg import bot, dp, save_message, data_base, get_most_similar_strings, get_now_datetime
from expenses import Expense
from handlers.roles import IsExpensesRole


PRODUCTS_RANGE = 3
MONEY_RECEPIENTS = ["Мириан", "Никита", "Другое"]
OTHER_PURPOSES_FOR_MONEY_OUT = ["Зарплата", "Самостоятельная докупка продуктов", "Другие траты"]



class ExpensesStates(StatesGroup):
    INITIAL_STATE = State()
    WAITING_SUPPLY_NAME = State()
    WAITING_CATEGORY_NAME = State()
    WAITING_FOR_SUPPLY_SUM = State()
    WAITING_FOR_SUPPLY_ENTER_WITH_HINTS = State()
    WAITING_FOR_FIRST_RESPONSE = State()
    WAITING_FOR_SECOND_RESPONSE = State()
    WAITING_FOR_THIRD_RESPONSE = State()


async def expenses_string(expenses: List[Expense]) -> str:
    #ps = poster_storage.PosterStorage()
    result = ""
    for exp in expenses:
        result += f"{exp.category}: {exp.amount}\n"
    return result


# @dp.message_handler(IsExpensesRole())
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


def get_keyboard(texts: List[str]):
    keyboard = aiogram.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = [KeyboardButton(text=text) for text in texts]
    keyboard.add(*buttons)
    return keyboard


def get_initial_keyboard():
    buttons = ["Ввести траты"]
    return get_keyboard(buttons)


# @dp.message_handler(IsExpensesRole())
# async def add(message: types.Message):
#     product = product_storage.parse_add_product_message(message.text)
#     product_storage.add_product(product.name, product.measurement_unit)
#     await message.answer(f"Добавил: {product.name}\nРазмерность: {product.measurement_unit}")


# @dp.message_handler(IsExpensesRole(), lambda message: message.text == "Список продуктов")
# async def products(message: types.Message):
#     interval = re.search("\d+-\d+", message.text)
#     ids = []
#     if interval:
#         fr, to = re.findall("\d+", interval.group())
#         ids = list(range(int(fr), int(to) + 1))
#     products = product_storage.get_products(ids)
#     answer = "\n" + "\n".join([f"{pr.id}: {pr.name}" for pr in products])
#     await message.answer(f"Продукты: {answer}")


def create_range_keyboard(names: List[str]) -> ReplyKeyboardMarkup:
    previous_range = []
    next_range = []
    keyboard = get_keyboard(previous_range + names + next_range)
    texts = ["Показать траты", "Назад", "В начало"]
    buttons = [KeyboardButton(text=text) for text in texts]
    keyboard.add(*buttons)
    return keyboard


async def get_products_keyboard(products_range: str, products_category: Optional[str]=None):
    from_id, to_id = re.findall("\d+", products_range)
    ids = list(range(int(from_id), int(to_id)+1))
    min_id = min(ids)
    max_id = max(ids)
    #ps = poster_storage.PosterStorage()
    #products = await ps.get_products(min_id, max_id)
    products = product_storage.get_products_by_category(products_category)
    products = products[min_id: max_id + 1]
    names = [pr.name for pr in products]
    previous_range = [f"{max(0, min_id - PRODUCTS_RANGE)}-{min_id-1} <="]
    next_range = [f"=> {max_id + 1}-{max_id + PRODUCTS_RANGE}"]
    if len(products) != max_id - min_id + 1:
        next_range = []
    if min_id == 0:
        previous_range = []
    keyboard = get_keyboard(previous_range + names + next_range)
    texts = ["Категории", "Показать траты", "В начало"]
    buttons = [KeyboardButton(text=text) for text in texts]
    keyboard.add(*buttons)
    return keyboard


@dp.message_handler(IsExpensesRole(), lambda message: message.text in ["Ввести траты", "Категории"], state="*")
async def products_categories(message: types.Message, state: FSMContext):
    #ps = poster_storage.PosterStorage()
    #await ps.async_init()
    await ExpensesStates.WAITING_CATEGORY_NAME.set()
    data = await state.get_data()
    expenses_categories_sequence = data.get("expenses_categories_sequence", [])
    categories = product_storage.get_product_categories_expenses(expenses_categories_sequence)
    keyboard = get_keyboard(categories)
    keyboard.add(KeyboardButton(text="В начало"))
    await message.answer("Выберите категорию", reply_markup=keyboard)


@dp.message_handler(IsExpensesRole(),
                    lambda message: message.text == "Назад",
                    state=ExpensesStates.WAITING_CATEGORY_NAME)
async def choose_product(message: types.Message, state: FSMContext):
    data = await state.get_data()
    expenses_categories_sequence = data.get("expenses_categories_sequence", [])
    if len(expenses_categories_sequence) < 1:
        await state.reset_state()
        await ExpensesStates.INITIAL_STATE.set()
        await message.answer("Выберите действие", reply_markup=get_initial_keyboard())
        return

    expenses_categories_sequence = expenses_categories_sequence[:-1]
    await state.update_data(expenses_categories_sequence=expenses_categories_sequence)
    categories = product_storage.get_product_categories_expenses(expenses_categories_sequence)
    if categories:
        keyboard = create_range_keyboard(categories)
        #keyboard.add(KeyboardButton(text="Назад"))
        await message.answer("Выберите", reply_markup=keyboard)
    else:
        await ExpensesStates.INITIAL_STATE.set()
        await message.answer("Выберите действие", reply_markup=get_initial_keyboard())


@dp.message_handler(IsExpensesRole(), lambda message: message.text == "Показать траты", state="*")
async def show_shipment(message: types.Message, state: FSMContext):
    #ps = poster_storage.PosterStorage()
    data = await state.get_data()
    expenses = data.get("expenses", [])
    if not expenses:
        keyboard = create_range_keyboard(["Ввести траты"])
        # await ps.async_init()
        # await ExpensesStates.WAITING_SUPPLY_NAME.set()
        await message.answer("Вы ничего не ввели", reply_markup=keyboard)
    else:
        keyboard = get_keyboard(["Отправить траты", "Ввести траты"])
        answer = await expenses_string(expenses)
        await message.answer(answer, reply_markup=keyboard)
    #await ps.async_init()
    #await ExpensesStates.WAITING_SUPPLY_NAME.set()


@dp.message_handler(IsExpensesRole(), lambda message: message.text == "Отправить траты", state="*")
async def send_shipment(message: types.Message, state: FSMContext):
    #ps = poster_storage.PosterStorage()
    data = await state.get_data()
    expenses = data.get("expenses", [])
    if not expenses:
        keyboard = get_keyboard(["Ввести траты"])
        await message.answer("Вы не ввели траты", reply_markup=keyboard)
    else:
        for expense in expenses:
            expenses_module.add_expense(expense)
        #await ps.increment_products(product_increments)
        await state.reset_state()
        keyboard = get_initial_keyboard()
        await ExpensesStates.INITIAL_STATE.set()
        await message.answer(f"Отправлены траты на сумму {expenses_module.expenses_sum(expenses)}", reply_markup=keyboard)


@dp.message_handler(IsExpensesRole(), lambda message: message.text == "В начало", state="*")
async def send_shipment(message: types.Message, state: FSMContext):
    keyboard = get_initial_keyboard()
    await state.reset_state()
    await ExpensesStates.INITIAL_STATE.set()
    await message.answer("Выберите действие", reply_markup=keyboard)


@dp.message_handler(IsExpensesRole(), state=ExpensesStates.WAITING_CATEGORY_NAME)
async def choose_product(message: types.Message, state: FSMContext):
    products_category = message.text
    data = await state.get_data()
    expenses_categories_sequence = data.get("expenses_categories_sequence", [])
    expenses_categories_sequence.append(products_category)
    categories = product_storage.get_product_categories_expenses(expenses_categories_sequence)
    if categories:
        await state.update_data(expenses_categories_sequence=expenses_categories_sequence)
        keyboard = create_range_keyboard(categories)
        #keyboard.add(KeyboardButton(text="Назад"))
        await message.answer("Выберите", reply_markup=keyboard)
        return
    expense_name = message.text
    #ps = poster_storage.PosterStorage()
    #await ps.async_init()
    await state.update_data(current_expense=expense_name)
    await message.answer(f"Для {expense_name} введите потраченную сумму:")
    await ExpensesStates.WAITING_FOR_SUPPLY_SUM.set()


def get_products_names_most_similar(name, num: int):
    products = product_storage.get_products()
    names = [p.name for p in products]
    return get_most_similar_strings(name, names)[:num]


# @dp.message_handler(IsExpensesRole(),
#                     lambda message: re.search("\d+-\d+", message.text),
#                     state=ExpensesStates.WAITING_SUPPLY_NAME)
# async def _(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     category_name = data.get("products_category")
#     text = re.search("\d+-\d+", message.text).group()
#     fr, to = re.findall("\d+", text)
#     keyboard = await get_products_keyboard(f"{int(fr)}-{int(to)}", category_name)
#     await state.update_data(current_products_range=f"{fr}-{to}")
#     sent_message = await message.answer(f"Продукты номер {fr}-{to}", reply_markup=keyboard)

#
# @dp.message_handler(IsExpensesRole(),
#                     state=ExpensesStates.WAITING_SUPPLY_NAME)
# async def chose_name(message: types.Message, state: FSMContext):
#     name = message.text
#     #ps = poster_storage.PosterStorage()
#     #product = await ps.product_by_name(name)
#     product = product_storage.get_product_by_name(name)
#
#     if not product:
#         await message.answer("Пожалуйста выберите из предложенных",
#                              reply_markup=await get_products_keyboard(f"0-{PRODUCTS_RANGE}"))
#         return
#
#     await state.update_data(current_product=product,
#                             product_name=product.name)
#     await message.answer(f"Для {product.name} введите количество {product.measurement_unit}:")
#     await ExpensesStates.WAITING_SUPPLY_QUANTITY.set()


@dp.message_handler(IsExpensesRole(),
                    state=ExpensesStates.WAITING_FOR_SUPPLY_SUM)
async def chose_quantity(message: types.Message, state: FSMContext):
    quantity = re.match(r'^[+-]?\d+(\.\d+)?$', message.text)
    if not quantity:
        await message.answer("Введите число в формате 331.12 или 232")
        return
    quantity = quantity.group()
    #ps = poster_storage.PosterStorage()

    data = await state.get_data()
    current_expense = data.get("current_expense")
    if not current_expense:
        return
    expense = Expense(float(quantity), current_expense, message.from_user.id, get_now_datetime())
    expenses = data.get("expenses", [])
    expenses.append(expense)
    expenses_categories_sequence = data.get("expenses_categories_sequence", [])
    categories = product_storage.get_product_categories_expenses(expenses_categories_sequence)
    keyboard = create_range_keyboard(categories)
    await state.update_data(expenses=expenses)

    await message.answer(f"Для добавил в трату {quantity} лари на {current_expense}",
                         reply_markup=keyboard)
    await ExpensesStates.WAITING_CATEGORY_NAME.set()


# @dp.message_handler(IsExpensesRole(), lambda message: message.text == "Ввести траты")
# async def products(message: types.Message, state: FSMContext):
#     await state.update_data(product_increments=[])
#     #ps = poster_storage.PosterStorage()
#     #await ps.async_init()
#     await ExpensesStates.WAITING_SUPPLY_NAME.set()
#     keyboard = await get_products_keyboard(f"0-{PRODUCTS_RANGE}")
#     await message.answer("Выберите продукт", reply_markup=keyboard)

#
# @dp.message_handler(IsExpensesRole(), commands=["sh"])
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
#             await message.answer(f"Добавили траты для {added_response}")
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


# @dp.message_handler(IsExpensesRole(), state=ExpensesStates.WAITING_FOR_SUPPLY_ENTER_WITH_HINTS)
# async def shipment(message: types.Message, state: FSMContext):
#     try:
#         save_message(data_base, message)
#         await message.answer(f"Введите траты в формате 100 яйца 2 нори")
#         await ExpensesStates.WAITING_FOR_FIRST_RESPONSE.set()
#         return
#     except exceptions.NotCorrectMessage as e:
#         await message.answer(str(e))
#         return

#
# @dp.message_handler(IsExpensesRole(), state=ExpensesStates.WAITING_FOR_FIRST_RESPONSE)
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
#         await message.answer(f"Добавили траты для {added_response}")
#         #await message.answer(f"Не добавили: {not_added_response}")
#         #await state.update_data(previous_message=message.text)
#         #await ExpensesStates.WAITING_FOR_SECOND_RESPONSE.set()
#         return
#     except exceptions.NotCorrectMessage as e:
#         await message.answer(str(e))
#         return

#
# @dp.message_handler(IsExpensesRole(), state=ExpensesStates.WAITING_FOR_SECOND_RESPONSE)
# async def shipment_2(message: types.Message, state: FSMContext):
#     try:
#         save_message(data_base, message)
#         data = await state.get_data()
#         previous_message_text = data["previous_message"]
#
#
#         #await ExpensesStates.WAITING_FOR_SECOND_RESPONSE.set()
#         return
#     except exceptions.NotCorrectMessage as e:
#         await message.answer(str(e))
#         return


@dp.message_handler(IsExpensesRole())
async def expenses_start(message: types.Message, state: FSMContext):
    await state.reset_state()
    await ExpensesStates.INITIAL_STATE.set()
    keyboard = get_initial_keyboard()
    await message.answer("Выберите действие", reply_markup=keyboard)


@dp.message_handler(IsExpensesRole(), state=ExpensesStates.INITIAL_STATE)
async def expenses_start(message: types.Message, state: FSMContext):
    await state.reset_state()
    keyboard = get_initial_keyboard()
    await message.answer("Выберите действие", reply_markup=keyboard)
