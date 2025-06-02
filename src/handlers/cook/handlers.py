import re
from typing import List

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import aiogram

import product_storage
from domain.product import ProductVolume
#import poster_storage
#from poster_storage import PosterStorage, ProductVolume, Product
from pkg import dp, get_most_similar_strings, get_now_date, ActionType
from src.handlers.roles import IsCookRole


PRODUCTS_RANGE = 3
MONEY_RECEPIENTS = ["Мириан", "Никита", "Другое"]
OTHER_PURPOSES_FOR_MONEY_OUT = ["Зарплата", "Самостоятельная докупка продуктов", "Другие траты"]


def measurement_unit_compose(unit: str) -> str:
    if unit in ("кг"):
        return "г"

    if unit in ("л"):
        return "мл"

    return unit


def measurement_unit_decompose(product_real_unit: str, amount: float) -> float:
    coefficient = 1

    composed_unit = measurement_unit_compose(product_real_unit)
    if composed_unit != product_real_unit:
        coefficient = 1000

    return amount / coefficient


MEASUREMENT_UNIT_DECOMPOSITION = {
    "г": "г",
    "кг": "г",
    "л": "мл",
    "мл": "мл"
}


class CookStates(StatesGroup):
    INITIAL_STATE = State()
    WAITING_SUPPLY_NAME = State()
    WAITING_CATEGORY_NAME = State()
    WAITING_SUPPLY_QUANTITY = State()
    WAITING_FOR_SUPPLY_ENTER_WITH_HINTS = State()
    WAITING_FOR_FIRST_RESPONSE = State()
    WAITING_FOR_SECOND_RESPONSE = State()
    WAITING_FOR_THIRD_RESPONSE = State()


async def _back_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    categories_sequence = data.get("categories_sequence", [])
    if len(categories_sequence) == 0:
        await state.reset_state()
        await CookStates.set()
        await message.answer("Выберите действие", reply_markup=get_initial_keyboard())
        return

    await CookStates.WAITING_CATEGORY_NAME.set()
    categories_sequence = categories_sequence[:-1]
    await state.update_data(categories_sequence=categories_sequence)
    categories = product_storage.get_product_categories(categories_sequence)
    if categories:
        keyboard = create_range_keyboard(f"0-{PRODUCTS_RANGE}", categories)
        # keyboard.add(KeyboardButton(text="Назад"))
        await message.answer("Выберите", reply_markup=keyboard)
    else:
        await CookStates.INITIAL_STATE.set()
        await message.answer("Выберите действие", reply_markup=get_initial_keyboard())


class WriteOffProductVolume:
    def __init__(self, product_id: int, write_off_quantity: int):
        self.write_off_volume = write_off_quantity
        product = product_storage.get_product_by_id(product_id)
        self.name = product.name
        self.original_measurement_unit = product.measurement_unit
        self.multiplyer = 1
        if self.original_measurement_unit.lower() in ["кг", "л"]:
            self.multiplyer = 1000
        self.measurement_unit = MEASUREMENT_UNIT_DECOMPOSITION[self.original_measurement_unit]

    @property
    def storage_volume(self) -> float:
        return float(self.write_off_volume)/self.multiplyer

def quantity(self):
    pass


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


# @dp.message_handler(IsCookRole())
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
    buttons = ["Ввести списание", "Ввести от руки"]
    return get_keyboard(buttons)


@dp.message_handler(IsCookRole(), commands=["start"], state="*")
async def cook_start(message: types.Message, state: FSMContext):
    await state.reset_state()
    await CookStates.INITIAL_STATE.set()
    keyboard = get_initial_keyboard()
    await message.answer("Выберите действие", reply_markup=keyboard)


@dp.message_handler(IsCookRole(), lambda message: message.text == "Список продуктов")
async def products(message: types.Message):
    interval = re.search("\d+-\d+", message.text)
    ids = []
    if interval:
        fr, to = re.findall("\d+", interval.group())
        ids = list(range(int(fr), int(to) + 1))
    products = product_storage.get_products(ids)
    answer = "\n" + "\n".join([f"{pr.id}: {pr.name}" for pr in products])
    await message.answer(f"Продукты: {answer}")


def create_range_keyboard(products_range: str, names: List[str]) -> ReplyKeyboardMarkup:
    previous_range = []
    next_range = []
    keyboard = get_keyboard(previous_range + names + next_range)
    texts = ["Показать списание", "Назад", "В начало"]
    buttons = [KeyboardButton(text=text) for text in texts]
    keyboard.add(*buttons)
    return keyboard


@dp.message_handler(IsCookRole(), lambda message: message.text in ["Ввести списание", "Категории"], state=CookStates.INITIAL_STATE)
async def products_categories(message: types.Message, state: FSMContext):
    #ps = poster_storage.PosterStorage()
    #await ps.async_init()
    await CookStates.WAITING_CATEGORY_NAME.set()
    data = await state.get_data()
    categories_sequence = data.get("categories_sequence", [])
    categories = product_storage.get_product_categories_cook(categories_sequence)
    keyboard = get_keyboard(categories)
    keyboard.add(KeyboardButton(text="В начало"))
    await message.answer("Выберите категорию", reply_markup=keyboard)


@dp.message_handler(IsCookRole(),
                    lambda message: message.text == "Назад",
                    state=CookStates.WAITING_CATEGORY_NAME)
async def choose_product(message: types.Message, state: FSMContext):
    data = await state.get_data()
    categories_sequence = data.get("categories_sequence", [])
    if len(categories_sequence) < 1:
        await state.reset_state()
        await CookStates.INITIAL_STATE.set()
        await message.answer("Выберите действие", reply_markup=get_initial_keyboard())
        return

    categories_sequence = categories_sequence[:-1]
    await state.update_data(categories_sequence=categories_sequence)
    categories = product_storage.get_product_categories_cook(categories_sequence)
    if categories:
        keyboard = create_range_keyboard(f"0-{PRODUCTS_RANGE}", categories)
        #keyboard.add(KeyboardButton(text="Назад"))
        await message.answer("Выберите", reply_markup=keyboard)
    else:
        await CookStates.INITIAL_STATE.set()
        await message.answer("Выберите действие", reply_markup=get_initial_keyboard())


@dp.message_handler(IsCookRole(), lambda message: message.text == "Показать списание", state="*")
async def show_shipment(message: types.Message, state: FSMContext):
    #ps = poster_storage.PosterStorage()
    data = await state.get_data()
    product_increments = data.get("product_increments", [])
    comment = data.get("comment", "Вы не добавляли комментарий")
    if not product_increments:
        keyboard = get_keyboard(["Ввести списание"])
        # await ps.async_init()
        # await CookStates.WAITING_SUPPLY_NAME.set()
        await message.answer("Списание пусто", reply_markup=keyboard)
    else:
        keyboard = get_keyboard(["Отправить списание", "Ввести списание", "Добавить комментарий"])
        answer = await _increments_string(product_increments)
        answer += f"\nКомментарий:\n{comment}"
        await message.answer(answer, reply_markup=keyboard)
    #await ps.async_init()
    #await CookStates.WAITING_SUPPLY_NAME.set()


@dp.message_handler(IsCookRole(), lambda message: message.text == "Отправить списание", state="*")
async def send_shipment(message: types.Message, state: FSMContext):
    #ps = poster_storage.PosterStorage()
    data = await state.get_data()
    product_increments = data.get("product_increments", [])
    if not product_increments:
        keyboard = get_keyboard(["Ввести списание"])
        await message.answer("Списание пусто", reply_markup=keyboard)
    else:
        product_storage.increment_products(product_increments,
                                           message.from_user.id,
                                           ActionType.WRITE_OFF,
                                           get_now_date())
        #await ps.increment_products(product_increments)
        await state.update_data(product_increments=[])
        keyboard = get_initial_keyboard()
        await CookStates.INITIAL_STATE.set()
        await message.answer("Списание отправлено", reply_markup=keyboard)


@dp.message_handler(IsCookRole(), lambda message: message.text == "В начало", state="*")
async def send_shipment(message: types.Message, state: FSMContext):
    keyboard = get_initial_keyboard()
    await state.reset_state()
    await CookStates.INITIAL_STATE.set()
    await message.answer("Выберите действие", reply_markup=keyboard)


@dp.message_handler(IsCookRole(), state=CookStates.WAITING_CATEGORY_NAME)
async def choose_product(message: types.Message, state: FSMContext):
    products_category = message.text
    data = await state.get_data()
    categories_sequence = data.get("categories_sequence", [])
    categories_sequence.append(products_category)
    categories = product_storage.get_product_categories_cook(categories_sequence)
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
    await message.answer(f"Для {product.name} введите количество {measurement_unit_compose(product.measurement_unit)}:")
    await CookStates.WAITING_SUPPLY_QUANTITY.set()


def get_products_names_most_similar(name, num: int):
    products = product_storage.get_products()
    names = [p.name for p in products]
    return get_most_similar_strings(name, names)[:num]


@dp.message_handler(IsCookRole(),
                    state=CookStates.WAITING_SUPPLY_QUANTITY)
async def chose_quantity(message: types.Message, state: FSMContext):
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
    categories = product_storage.get_product_categories_cook(categories_sequence)
    keyboard = create_range_keyboard(products_range, categories)
    product_name = data['current_product'].name
    product = product_storage.get_product_by_name(product_name)
    #product = await ps.product_by_name(name)
    current_product = data['current_product']
    pi = ProductVolume(product.id, measurement_unit_decompose(current_product.measurement_unit, -abs(quantity)))
    #pi = poster_storage.ProductVolume(product.id, quantity)
    product_increments.append(pi)
    await state.update_data(product_increments=product_increments)
    #await ps.increment_products([poster_storage.ProductVolume(product.id, quantity)])
    #product_storage.increment(name, quantity)
    await message.answer(f"Для {product_name} добавил в списание {quantity} {measurement_unit_compose(current_product.measurement_unit)}",
                         reply_markup=keyboard)
    await CookStates.WAITING_CATEGORY_NAME.set()


@dp.message_handler(IsCookRole(), state=None)
async def cook_start(message: types.Message, state: FSMContext):
    await state.reset_state()
    await CookStates.INITIAL_STATE.set()
    keyboard = get_initial_keyboard()
    await message.answer("Выберите действие", reply_markup=keyboard)


class ReceivingByHandStates(StatesGroup):
    WAITING_SUPPLY_NAME = State()
    WAITING_SUPPLY_QUANTITY = State()
    WAITING_CATEGORY_NAME = State()
    WAITING_FOR_COMMENT = State()


@dp.message_handler(IsCookRole(),
                    lambda message: message.text == "Ввести от руки",
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
        await message.answer(f"Для {product.name} введите количество {measurement_unit_compose(product.measurement_unit)}:")
        await state.update_data(current_product=product)
        return

    names = get_products_names_most_similar(sub_name, 5)
    keyboard = get_keyboard(names)
    keyboard.add(KeyboardButton(text="Назад"))
    await message.answer(f"Выберите из предложенных или повторите попытку", reply_markup=keyboard)


@dp.message_handler(IsCookRole(),
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
    quantity = -abs(float(message.text))
    categories_sequence = data.get("categories_sequence", [])
    product = data['current_product']
    #product = product_storage.get_product_by_name(product_name)
    current_product = data['current_product']
    pi = ProductVolume(product.id, measurement_unit_decompose(current_product.measurement_unit, quantity))
    #pi = poster_storage.ProductVolume(product.id, quantity)
    product_increments.append(pi)
    await state.update_data(product_increments=product_increments)
    #await ps.increment_products([poster_storage.ProductVolume(product.id, quantity)])
    #product_storage.increment(name, quantity)
    keyboard = get_initial_keyboard()
    keyboard.add(KeyboardButton(text="Показать списание"))
    keyboard.add(KeyboardButton(text="Добавить комментарий"))
    await message.answer(f"Для {product.name} добавил в списание {quantity}"
                         f" {measurement_unit_compose(current_product.measurement_unit)}", reply_markup=keyboard)
    await ReceivingByHandStates.WAITING_SUPPLY_NAME.set()


@dp.message_handler(IsCookRole(), lambda message: message.text == "Показать списание", state=ReceivingByHandStates.WAITING_SUPPLY_NAME)
async def show_shipment(message: types.Message, state: FSMContext):
    #ps = poster_storage.PosterStorage()
    data = await state.get_data()
    product_increments = data.get("product_increments", [])
    if not product_increments:
        keyboard = get_keyboard(["Ввести списание"])
        # await ps.async_init()
        # await ReceivingStates.WAITING_SUPPLY_NAME.set()
        await message.answer("Списание пусто", reply_markup=keyboard)
    else:
        keyboard = get_keyboard(["Отправить списание", "Ввести от руки"])
        answer = await _increments_string(product_increments)
        await message.answer(answer, reply_markup=keyboard)
    #await ps.async_init()
    #await ReceivingStates.WAITING_SUPPLY_NAME.set()


@dp.message_handler(IsCookRole(), lambda message: message.text == "Добавить комментарий", state=ReceivingByHandStates.WAITING_SUPPLY_NAME)
async def add_comment(message: types.Message, state: FSMContext):
    #ps = poster_storage.PosterStorage()
    await ReceivingByHandStates.WAITING_FOR_COMMENT.set()
    await message.answer("Напишите комментарий к аномалиям или процессу:")


@dp.message_handler(IsCookRole(),
                    state=ReceivingByHandStates.WAITING_FOR_COMMENT)
async def add_comment_2(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    keyboard = get_initial_keyboard()
    keyboard.add(KeyboardButton(text="Показать списание"))
    keyboard.add(KeyboardButton(text="Добавить комментарий"))
    await ReceivingByHandStates.WAITING_SUPPLY_NAME.set()
    await message.answer("Комментарий к списанию добавлен", reply_markup=keyboard)


@dp.message_handler(IsCookRole(), lambda message: message.text == "Отправить списание", state=ReceivingByHandStates.WAITING_SUPPLY_NAME)
async def send_shipment(message: types.Message, state: FSMContext):
    #ps = poster_storage.PosterStorage()
    data = await state.get_data()
    product_increments = data.get("product_increments", [])
    comment = data.get("comment", "")
    if not product_increments:
        keyboard = get_keyboard(["Ввести списание"])
        await message.answer("Списание пусто", reply_markup=keyboard)
    else:
        product_storage.increment_products(product_increments,
                                           message.from_user.id,
                                           ActionType.RECEIVING,
                                           date=get_now_date(),
                                           comment=comment)
        #await ps.increment_products(product_increments)
        await state.update_data(product_increments=[])
        keyboard = get_initial_keyboard()
        await CookStates.INITIAL_STATE.set()
        await message.answer("Списание отправлено", reply_markup=keyboard)


@dp.message_handler(IsCookRole(), state=ReceivingByHandStates.WAITING_SUPPLY_NAME)
async def choose_product(message: types.Message, state: FSMContext):
    return await _get_most_similar(message, state)
