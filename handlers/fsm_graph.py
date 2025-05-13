# fsm_graph.py
from aiogram.fsm.state import State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import StatesGroup, State
from transitions.extensions import GraphMachine


class PizzaOrderStates(StatesGroup):
    category = State()
    size = State()
    confirmation = State()


def _convert_fsm_graph(fsm_graph: dict):
    transitions = []
    states = set()

    for source_state_, options in fsm_graph.items():
        source_state = str(source_state_)  # Преобразуем в строку
        states.add(source_state)
        for trigger, dest_state_ in options.items():
            if dest_state_:
                dest_state = str(dest_state_)  # Преобразуем в строку
                states.add(dest_state)
            transitions.append({
                "trigger": trigger,
                "source": source_state,
                "dest": dest_state if dest_state_ else None
            })

    return list(states), transitions





class FSM:
    def __init__(self, fsm_graph, model=None):
        self._graph = fsm_graph
        self._model = model
        self._machine = None
        self._re_init()

    def add_state(self, transition_dict: dict):
        self._graph.update(transition_dict)

    def _re_init(self):
        states, transitions = _convert_fsm_graph(self._graph)
        if self._model:
            self._machine = GraphMachine(model=self._model, states=states, transitions=transitions)
        else:
            self._machine = GraphMachine(states=states, transitions=transitions)

    def apply(self, text: str):
        self._machine.trigger(text)
        print(self._machine.state)
