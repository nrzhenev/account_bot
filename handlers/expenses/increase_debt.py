import aiogram
import re
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import KeyboardButton
from handlers.expenses.initial_handlers import ExpensesInitialStates, INITIAL_POSSIBILITIES, RETURN_BUTTON, process_quantity

from handlers.roles import IsExpensesRole
# import poster_storage
# from poster_storage import PosterStorage, ProductVolume, Product
from pkg import dp

MODULE_NAME = "increase_debt"


class DebtStates(StatesGroup):
    WAITING_CHOOSE_DEBT_ACTION = State()
    WAITING_CHOOSE_DEBT_ACTOR = State()
    WAITING_OTHER_DEBT_ACTOR = State()
    WAITING_DEBT_QUANTITY = State()


OTHER_ACTOR_BUTTON = "Другое"
DEBT_ACTORS = ["Два Брата", "Gold pack", "Сыр", "Ростислав", "Гоча упаковки", "Овощи", OTHER_ACTOR_BUTTON]
DEBT_ACTIONS = ["Увеличить долг", "Уменьшить долг"]


def keyboard_with_return_button(names: list):
    keyboard = aiogram.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = [KeyboardButton(text=text) for text in names + [RETURN_BUTTON]]
    return keyboard.add(*buttons)


@dp.message_handler(IsExpensesRole(),
                    lambda message: message.text == INITIAL_POSSIBILITIES[MODULE_NAME],
                    state=ExpensesInitialStates.INITIAL_STATE)
async def debt_initial_actions(message: types.Message, state: FSMContext):
    """Предложить пользователю выбрать из списка категорий"""

    keyboard = keyboard_with_return_button(["Увеличить долг", "Уменьшить долг"])
    await message.answer("Выберите действие", reply_markup=keyboard)
    await DebtStates.WAITING_CHOOSE_DEBT_ACTION.set()


@dp.message_handler(IsExpensesRole(),
                    lambda message: message.text in DEBT_ACTIONS,
                    state=DebtStates.WAITING_CHOOSE_DEBT_ACTION)
async def handle_category_other(message: types.Message, state: FSMContext):
    await state.update_data(debt_action=message.text)
    await DebtStates.WAITING_CHOOSE_DEBT_ACTOR.set()
    keyboard = keyboard_with_return_button(DEBT_ACTORS)
    await message.answer(f"Выберите кому {message.text.lower()}", reply_markup=keyboard)


@dp.message_handler(IsExpensesRole(),
                    lambda message: message.text == OTHER_ACTOR_BUTTON,
                    state=DebtStates.WAITING_CHOOSE_DEBT_ACTOR)
async def handle_debt_actor_other(message: types.Message, state: FSMContext):
    await DebtStates.WAITING_OTHER_DEBT_ACTOR.set()
    keyboard = keyboard_with_return_button([])
    await message.answer("Введите название контрагента", reply_markup=keyboard)


@dp.message_handler(IsExpensesRole(),
                    lambda message: message.text != OTHER_ACTOR_BUTTON,
                    state=[DebtStates.WAITING_CHOOSE_DEBT_ACTOR, DebtStates.WAITING_OTHER_DEBT_ACTOR])
async def handle_category_other(message: types.Message, state: FSMContext):
    await state.update_data(debt_actor=message.text)
    await DebtStates.WAITING_DEBT_QUANTITY.set()
    await message.answer(f"Выберите сумму в лари")


@dp.message_handler(IsExpensesRole(),
                    state=DebtStates.WAITING_DEBT_QUANTITY)
async def process_debt_quantity(message: types.Message, state: FSMContext):
    quantity = await process_quantity(message)
    if quantity is None:
        return

    data = await state.get_data()
    debt_actor = data["debt_actor"]
    debt_action = data.get("debt_action", "")
    action_text = "увеличен" if "Увеличить" in debt_action else "уменьшен"
    
    await message.answer(f"Долг у {debt_actor} {action_text} на {quantity} лари")
    await ExpensesInitialStates.INITIAL_STATE.set()
