from typing import Optional

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State

from src.auxiliary.fsm import FSM


class StateWithData(State):
    def __init__(self, message: Optional[str]=None, reply_markup: Optional[str]=None):
        self.message = message
        self.reply_markup = reply_markup
        super().__init__()



class MessageHandler:
    def __init__(self, initial_state: StateWithData):
        self.fsm = FSM(initial_state.state)
        self.state_messages = {}
        self.state_reply_markups = {}
        self.states = {}

    def add_transition(self, from_state: StateWithData, to_state: StateWithData, key: Optional[str]=None):
        self._add_state(from_state)
        self._add_state(to_state)
        self.fsm.add_transition(from_state.state, to_state.state, key)

    def _add_state(self, state: StateWithData):
        self.states[state.state] = state

    def _get_state(self, state_key: str) -> Optional[StateWithData]:
        return self.states.get(state_key)

    async def handle_state_transition(self, message, context: FSMContext):
        previous_state_key = self.fsm.state
        self.fsm.move(message.text)
        current_state_key = self.fsm.state

        current_state = self._get_state(current_state_key)
        if previous_state_key != current_state_key:
           await context.set_state(current_state)

        if current_state is None:
            raise ValueError("Нет нужного state")

        if current_state.message and current_state.reply_markup:
            return await message.answer(current_state.message, reply_markup=current_state.reply_markup)
        elif current_state.message:
            return await message.answer(current_state.message)
        else:
            return
