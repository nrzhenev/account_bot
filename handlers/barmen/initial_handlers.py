from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import StatesGroup, State

from handlers.roles import IsShipmentsRole
from pkg import get_keyboard, ACCESS_IDS
from middlewares import AccessMiddleware

# Создаем роутер для обработчиков бармена
barmen_router = Router()
barmen_router.message.middleware(AccessMiddleware(allowed_user_ids=ACCESS_IDS))


class BarmenInitialStates(StatesGroup):
    INITIAL_STATE = State()
    WAITING_CHOOSE_INITIAL_ACTION = State()
    SHIPMENT_INITIAL_STATE = State()


# Применяем миддлварь проверки роли
barmen_router.message.filter(IsShipmentsRole())


@barmen_router.message(Command(commands=["start"]))
async def barmen_start(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(BarmenInitialStates.WAITING_CHOOSE_INITIAL_ACTION)
    keyboard = get_initial_keyboard()
    await message.answer("Выберите действие", reply_markup=keyboard)


@barmen_router.message(StateFilter(BarmenInitialStates.INITIAL_STATE))
async def barmen_back(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(BarmenInitialStates.WAITING_CHOOSE_INITIAL_ACTION)
    keyboard = get_initial_keyboard()
    await message.answer("Выберите действие", reply_markup=keyboard)


@barmen_router.message(StateFilter(BarmenInitialStates.WAITING_CHOOSE_INITIAL_ACTION))
async def process_choose_action(message: types.Message, state: FSMContext):
    # Здесь должен быть код обработки выбора действия
    pass


def get_initial_keyboard():
    buttons = ["Ввести поставки", "Пополнение наличных", "Выдача наличных", "Ввести поставки от руки"]
    return get_keyboard(buttons)


