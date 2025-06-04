import re

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup

from src.handlers.expenses.initial_handlers import ExpensesInitialStates, keyboard_with_return_button, expenses_event, \
    expenses_mh, expenses_router
from src.handlers.state_messages import StateWithData

MODULE_NAME = "add_expense"


EXPENSES_CATEGORIES = ["Панда закупки бармену",
                       "Мириан Личное",
                       "Такси/Бензин",
                       "Банк",
                       "Аренда",
                       "Коммунальные услуги",
                       "Другое"]


class ExpensesStates(StatesGroup):
    CHOOSING_PAYMENT_TYPE = StateWithData("Как было оплачено",
                                          keyboard_with_return_button(["Картой", "Наличными"]))
    CHOOSING_CATEGORY= StateWithData("Выберите категорию", keyboard_with_return_button(EXPENSES_CATEGORIES))
    CHOOSING_QUANTITY = StateWithData("Введите число (сколько потрачено)")
    WAITING_CATEGORY_NAME = StateWithData()
    WAITING_OTHER_CATEGORY_NAME = StateWithData()


expenses_mh.add_transition(ExpensesInitialStates.WAITING_CHOOSE_ACTION, ExpensesStates.CHOOSING_PAYMENT_TYPE, "Ввести траты")
expenses_mh.add_transition(ExpensesStates.CHOOSING_PAYMENT_TYPE, ExpensesStates.CHOOSING_CATEGORY)
expenses_mh.add_transition(ExpensesStates.CHOOSING_CATEGORY, ExpensesStates.CHOOSING_QUANTITY)


@expenses_router.message(ExpensesStates.CHOOSING_PAYMENT_TYPE)
@expenses_event
async def choosing_payment_type(message: types.Message, state: FSMContext):
    payment_type = message.text
    await state.update_data({"payment_type": payment_type})


@expenses_router.message(ExpensesStates.CHOOSING_CATEGORY)
@expenses_event
async def choosing_category(message: types.Message, state: FSMContext):
    category = message.text
    await state.update_data({"category": category})


@expenses_router.message(ExpensesStates.CHOOSING_QUANTITY)
@expenses_event
async def define_quantity(message: types.Message, state: FSMContext):
    quantity = re.match(r'^[+-]?\d+(\.\d+)?$', message.text)
    if not quantity:
        await message.answer("Введите число в формате 331.12 или 232")
        return -1

    quantity = float(quantity.group())
    data = await state.get_data()
    await state.update_data({"quantity": quantity})
    await message.answer(f"Добавлена трата <b>{quantity}</b> лари через <b>{data.get('payment_type')}</b> на <b>{data.get('category')}</b>", parse_mode="HTML")
