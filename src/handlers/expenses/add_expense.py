from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from src.handlers.expenses.initial_handlers import ExpensesInitialStates, INITIAL_POSSIBILITIES, \
    keyboard_with_return_button, process_quantity
from src.handlers.roles import IsExpensesRole
from pkg import dp

MODULE_NAME = "add_expense"


class ExpensesStates(StatesGroup):
    WAITING_CATEGORY_NAME = State()
    WAITING_OTHER_CATEGORY_NAME = State()
    WAITING_EXPENSE_QUANTITY = State()


EXPENSES_CATEGORIES = ["Мириан Личное", "Такси/Бензин", "Аренда", "Коммунальные услуги", "Другое"]


@dp.message_handler(IsExpensesRole(),
                    lambda message: message.text == INITIAL_POSSIBILITIES[MODULE_NAME],
                    state=ExpensesInitialStates.INITIAL_STATE)
async def category_request(message: types.Message, state: FSMContext):
    """Предложить пользователю выбрать из списка категорий"""

    await ExpensesStates.WAITING_CATEGORY_NAME.set()
    keyboard = keyboard_with_return_button(EXPENSES_CATEGORIES)
    await message.answer("Выберите категорию", reply_markup=keyboard)


@dp.message_handler(IsExpensesRole(),
                    lambda message: message.text == EXPENSES_CATEGORIES[-1],
                    state=ExpensesStates.WAITING_CATEGORY_NAME)
async def handle_category_other(message: types.Message, state: FSMContext):
    await ExpensesStates.WAITING_OTHER_CATEGORY_NAME.set()
    keyboard = keyboard_with_return_button([])
    await message.answer("На что потрачено", reply_markup=keyboard)


@dp.message_handler(IsExpensesRole(),
                    lambda message: message.text != EXPENSES_CATEGORIES[-1],
                    state=[ExpensesStates.WAITING_CATEGORY_NAME, ExpensesStates.WAITING_OTHER_CATEGORY_NAME])
async def process_category_name(message: types.Message, state: FSMContext):
    await state.update_data(expense_category=message.text)
    await ExpensesStates.WAITING_EXPENSE_QUANTITY.set()
    await message.answer(f"Введите, сколько потрачено, в формате  331.12 или 232")


@dp.message_handler(IsExpensesRole(),
                    state=ExpensesStates.WAITING_EXPENSE_QUANTITY)
async def process_expense_quantity(message: types.Message, state: FSMContext):
    quantity = await process_quantity(message)
    if quantity is None:
        return

    data = await state.get_data()
    category = data["expense_category"]
    await message.answer(f"Добавлено {quantity} лари в {category}")
    await ExpensesInitialStates.INITIAL_STATE.set()
