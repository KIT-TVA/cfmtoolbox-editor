from copy import deepcopy

class UndoRedoManager:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def add_state(self, cfm):
        self.undo_stack.append(deepcopy(cfm))
        self.redo_stack.clear()

    def undo(self):
        if len(self.undo_stack) > 1:
            current_state = self.undo_stack.pop()
            self.redo_stack.append(current_state)
            return deepcopy(self.undo_stack[-1])
        return None

    def redo(self):
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(state)
            return deepcopy(state)
        return None