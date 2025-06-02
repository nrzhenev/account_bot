from typing import Optional

from aiogram import types
from aiogram.fsm.context import FSMContext
from src.auxiliary.fsm import FSM
from aiogram.fsm.state import State


class StateMessagesHandler:
    def __init__(self):
        self.state_messages = {}
        self.state_reply_markups = {}

    def add_state_message(self, state: str, message: str, reply_markup=None):
        self.state_messages[state] = message
        if reply_markup:
            self.state_reply_markups[state] = reply_markup

    async def handle_set_state(self, incoming_message: types.Message, context: FSMContext):
        current_state = await context.get_state()
        reply_message = self.state_messages.get(current_state)
        reply_markup = self.state_reply_markups.get(current_state)
        if reply_message and reply_markup:
            return await incoming_message.answer(reply_message, reply_markup=reply_markup)
        elif reply_message:
            return await incoming_message.answer(reply_message)
        else:
            return


class MessageHandler:
    def __init__(self, initial_key: str):
        self.fsm = FSM(initial_key)
        self.state_message_handler = StateMessagesHandler()

    def add_state(self,
                  state: State,
                  set_state_message: Optional[str]=None,
                  set_state_markup=None):
        self.state_message_handler.add_state_message(state.state, set_state_message, set_state_markup)

    def add_transition(self, from_state: State, to_state: State, key: Optional[str]=None):
        self.fsm.add_transition(from_state.state, to_state.state, key)

    async def handle_state_transition(self, message, context: FSMContext):
        previous_state = self.fsm.state
        self.fsm.move(message.text)
        new_state = self.fsm.state
        if previous_state != new_state:
            await self.state_message_handler.handle_set_state(message, context)
        return
