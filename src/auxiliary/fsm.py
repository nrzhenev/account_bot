from collections import defaultdict
from typing import Optional
import abc

from transitions.extensions import GraphMachine


class StateTransitionInterface(abc.ABC):
    def trigger_transition(self, message, state):
        pass


class FSM:
    def __init__(self, initial_state_key: str):
        self._initial_state_key = initial_state_key
        self._transitions = []
        self._states = set()
        self._state_key_dict = defaultdict(list)
        self._default_transition_key = "_next_"
        self._default_back_key = "_back_"
        self._machine = None

    def add_transition(self, from_state: str, to_state: str, transition_key: Optional[str]=None):
        if transition_key is None:
            if self._state_key_dict.get(from_state):
                raise ValueError("Cannot use keyless transition for state with actual keys added")
            transition_key = self._default_transition_key
        else:
            if self._default_transition_key in self._state_key_dict.get(from_state, []):
                raise ValueError("Cannot set transition key for state without transition key")
        self._state_key_dict[from_state].append(transition_key)
        self._states.add(from_state)
        self._states.add(to_state)
        self._transitions.append({'trigger': transition_key, 'source': from_state, 'dest': to_state})
        self._transitions.append({'trigger': self._default_back_key, 'source': to_state, 'dest': from_state})
        if self._machine is not None:
            self._re_init()

    def _re_init(self):
        self._machine = GraphMachine(states=list(self._states), transitions=self._transitions, initial=self._initial_state_key, auto_transitions=False)

    def get_state_keys(self, state: str):
        state_keys = self._state_key_dict.get(state)
        if state_keys is None:
            print("State is not present")
        return state_keys

    def move(self, transition_key: Optional[str]=None):
        if self._machine is None:
            self._re_init()

        if transition_key is None or self._default_transition_key in self._state_key_dict.get(self.state):
            transition_key = self._default_transition_key

        try:
            self._machine.trigger(transition_key)
            print("moved to", self.state)
        #except MachineError as e:
        except Exception as e:
            print(f"There is no such key {transition_key}; Staying the same")

    @property
    def state(self) -> str:
        if not self._machine:
            return self._initial_state_key
        return self._machine.state

    def back(self):
        self.move(self._default_back_key)
