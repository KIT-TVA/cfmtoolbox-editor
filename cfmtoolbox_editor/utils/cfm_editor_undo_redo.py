from copy import deepcopy

from cfmtoolbox import CFM


class UndoRedoManager:
    def __init__(self):
        self.undo_stack: list[CFM] = []
        self.redo_stack: list[CFM] = []
        self.initial_state: CFM | None = None

    def add_state(self, cfm: CFM):
        self.undo_stack.append(deepcopy(cfm))
        self.redo_stack.clear()

    def undo(self) -> CFM | None:
        if len(self.undo_stack) > 1:
            current_state = self.undo_stack.pop()
            self.redo_stack.append(current_state)
            return deepcopy(self.undo_stack[-1])
        return None

    def redo(self) -> CFM | None:
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(state)
            return deepcopy(state)
        return None

    def set_initial_state(self, cfm: CFM):
        self.initial_state = deepcopy(cfm)

    def reset(self) -> CFM:
        assert self.initial_state is not None
        self.add_state(self.initial_state)
        return deepcopy(self.initial_state)
