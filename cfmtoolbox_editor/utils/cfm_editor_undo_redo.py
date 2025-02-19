"""
This module defines the UndoRedoManager class, which is responsible for managing the undo and redo
functionality for the feature model editor.

Classes:
    UndoRedoManager: A class to manage the undo and redo stacks for the feature model editor.
"""

from copy import deepcopy
from typing import Tuple, Dict

from cfmtoolbox import CFM


class UndoRedoManager:
    def __init__(self):
        """
        Initialize the UndoRedoManager with empty undo and redo stacks.
        """
        self.undo_stack: list[Tuple[CFM, Dict[str, bool]]] = []
        self.redo_stack: list[Tuple[CFM, Dict[str, bool]]] = []
        self.initial_state: Tuple[CFM, Dict[str, bool]] | None = None

    def add_state(self, cfm: CFM, expanded_features: Dict[str, bool]):
        """
        Add a new state to the undo stack and clear the redo stack.

        Args:
            cfm (CFM): The current state of the feature model.
            expanded_features (Dict[str, bool]): Contains expanded/collapsed state of features
        """
        self.undo_stack.append((deepcopy(cfm), deepcopy(expanded_features)))
        self.redo_stack.clear()

    def undo(self) -> Tuple[CFM, Dict[str, bool]] | None:
        """
        Undo the last action and return the previous state.

        Returns:
            Tuple[CFM, Dict[str, bool]] | None: The previous state of the feature model, or None if no undo is possible.
        """
        if len(self.undo_stack) > 1:
            current_state = self.undo_stack.pop()
            self.redo_stack.append(current_state)
            return deepcopy(self.undo_stack[-1])
        return None

    def redo(self) -> Tuple[CFM, Dict[str, bool]] | None:
        """
        Redo the last undone action and return the state.

        Returns:
            Tuple[CFM, Dict[str, bool]] | None: The redone state of the feature model, or None if no redo is possible.
        """
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(state)
            return deepcopy(state)
        return None

    def set_initial_state(self, cfm: CFM, expanded_features: Dict[str, bool]):
        """
        Set the initial state of the feature model.

        Args:
            cfm (CFM): The initial state of the feature model.
            expanded_features (Dict[str, bool]): Contains expanded/collapsed state of features
        """
        self.initial_state = (deepcopy(cfm), deepcopy(expanded_features))

    def reset(self) -> Tuple[CFM, Dict[str, bool]]:
        """
        Reset the feature model to its initial state.

        Returns:
            Tuple[CFM, Dict[str, bool]]: The initial state of the feature model.
        """
        assert self.initial_state is not None
        self.add_state(self.initial_state[0], self.initial_state[1])
        return deepcopy(self.initial_state)
