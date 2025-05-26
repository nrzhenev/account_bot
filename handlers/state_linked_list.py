class StateNode:
    def __init__(self, state):
        self.state = state
        self.prev = None
        self.next = None

class StateLinkedList:
    def __init__(self, states: list):
        self.head = StateNode(states[0])
        self.current = self.head
        for state in states[1:]:
            self.add_state(state)

    def add_state(self, state):
        new_node = StateNode(state)
        new_node.prev = self.current
        self.current.next = new_node
        self.current = new_node

    @property
    def next(self):
        if self.current.next:
            self.current = self.current.next
        else:
            self.current = self.head
        return self.state

    @property
    def previous(self):
        if self.current.prev:
            self.current = self.current.prev
        else:
            self.current = self.head
        return self.state

    @property
    def state(self):
        return self.current.state 