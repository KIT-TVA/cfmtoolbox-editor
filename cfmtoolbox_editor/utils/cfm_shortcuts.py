"""
This module defines the ShortcutManager class, which is responsible for managing keyboard shortcuts
for the feature model editor using the Tkinter library.

Classes:
    ShortcutManager: A class to manage keyboard shortcuts for the feature model editor.
"""

import platform


class ShortcutManager:
    def __init__(self, editor_app):
        """
        Initialize the ShortcutManager with the editor application instance.

        Args:
            editor_app: The editor application instance.
        """
        self.editor = editor_app
        self.is_mac = platform.system() == "Darwin"
        self._define_shortcuts()
        self._setup_shortcuts()

    def update_editor(self, editor_app):
        """
        Update the editor application instance.

        Args:
            editor_app: The new editor application instance.
        """
        self.editor = editor_app
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        root = self.editor.root
        root.bind(self.shortcuts["ADD_FEATURE"], self._handle_add_feature)
        root.bind(self.shortcuts["EDIT_FEATURE"], self._handle_edit)
        root.bind(self.shortcuts["DELETE_FEATURE"], self._handle_delete)
        root.bind(self.shortcuts["ADD_CONSTRAINT"], self._handle_add_constraint)
        root.bind(self.shortcuts["SAVE"], self._handle_save)
        root.bind(self.shortcuts["RESET"], self._handle_reset)
        root.bind(self.shortcuts["UNDO"], self._handle_undo)
        root.bind(self.shortcuts["REDO"], self._handle_redo)

    def _define_shortcuts(self):
        base = "Command" if self.is_mac else "Control"
        self.shortcuts = {
            "ADD_FEATURE": f"<{base}-n>",
            "EDIT_FEATURE": f"<{base}-e>",
            "DELETE_FEATURE": "<BackSpace>" if self.is_mac else "<Delete>",
            "ADD_CONSTRAINT": f"<{base}-a>",
            "SAVE": f"<{base}-s>",
            "RESET": f"<{base}-r>",
            "UNDO": f"<{base}-z>",
            "REDO": f"<{base}-y>",
        }
        self.accelerators = {
            "ADD_FEATURE": f"{base}+n",
            "EDIT_FEATURE": f"{base}+e",
            "DELETE_FEATURE": "BackSpace" if self.is_mac else "Delete",
            "ADD_CONSTRAINT": f"{base}+a",
            "SAVE": f"{base}+s",
            "RESET": f"{base}+r",
            "UNDO": f"{base}+z",
            "REDO": f"{base}+y",
        }

    def _handle_add_feature(self, event):
        if self.editor.get_currently_highlighted_feature() and hasattr(
            self.editor, "add_feature"
        ):
            self.editor.add_feature(self.editor.get_currently_highlighted_feature())

    def _handle_edit(self, event):
        if self.editor.get_currently_highlighted_feature() and hasattr(
            self.editor, "edit_feature"
        ):
            self.editor.edit_feature(self.editor.get_currently_highlighted_feature())

    def _handle_delete(self, event):
        if self.editor.get_currently_highlighted_feature() and hasattr(
            self.editor, "delete_feature"
        ):
            self.editor.delete_feature(self.editor.get_currently_highlighted_feature())

    def _handle_add_constraint(self, event):
        if self.editor.get_currently_highlighted_feature() and hasattr(
            self.editor, "add_constraint"
        ):
            self.editor.add_constraint(self.editor.get_currently_highlighted_feature())

    def _handle_save(self, event):
        if hasattr(self.editor, "save_model"):
            self.editor.save_model()

    def _handle_reset(self, event):
        if hasattr(self.editor, "reset_model"):
            self.editor.reset_model()

    def _handle_undo(self, event):
        if hasattr(self.editor, "undo"):
            self.editor.undo()

    def _handle_redo(self, event):
        if hasattr(self.editor, "redo"):
            self.editor.redo()
