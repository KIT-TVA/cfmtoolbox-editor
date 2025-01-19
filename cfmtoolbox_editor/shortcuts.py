import platform


class ShortcutManager:
    def __init__(self, editor_app):
        self.editor = editor_app
        self.is_mac = platform.system() == "Darwin"
        self._define_shortcuts()
        self._setup_shortcuts()

    def update_editor(self, editor_app):
        """Update the editor_app instance."""
        self.editor = editor_app
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        root = self.editor.root
        root.bind(self.shortcuts["NEW_CONSTRAINT"], self._handle_new)
        root.bind(self.shortcuts["EDIT_CONSTRAINT"], self._handle_edit)
        root.bind(self.shortcuts["DELETE_CONSTRAINT"], self._handle_delete)
        root.bind(self.shortcuts["SAVE"], self._handle_save)
        root.bind(self.shortcuts["RESET"], self._handle_reset)
        root.bind(self.shortcuts["UNDO"], self._handle_undo)
        root.bind(self.shortcuts["REDO"], self._handle_redo)

    def _define_shortcuts(self):
        print("Define Shortcuts")
        base = "Command" if self.is_mac else "<Control"
        self.shortcuts = {
            "NEW_CONSTRAINT": f"<{base}-n>",
            "EDIT_CONSTRAINT": f"<{base}-e>",
            "DELETE_CONSTRAINT": "<BackSpace>" if self.is_mac else "<Delete>",
            "SAVE": f"<{base}-s>",
            "RESET": f"<{base}-r>",
            "UNDO": f"<{base}-z>",
            "REDO": f"<{base}-y>",
        }
        self.accelerators = {"UNDO": f"{base}+z", "REDO": f"{base}+y"}

    def _handle_new(self, event):
        # TODO: By clicking on a feature, the feature should be editable
        print("Not yet implemented")

    def _handle_edit(self, event):
        # TODO: By clicking on a feature, the feature should be editable
        print("Not yet implemented")

    def _handle_delete(self, event):
        # TODO: By clicking on a feature, the feature should be deletable
        print("Not yet implemented")

    def _handle_save(self, event):
        if hasattr(self.editor, "_save_model"):
            self.editor._save_model()

    def _handle_reset(self, event):
        if hasattr(self.editor, "_reset_model"):
            self.editor._reset_model()
            print("Reset-Tastenkürzel ausgelöst")

    def _handle_undo(self, event):
        if hasattr(self.editor, "_undo"):
            self.editor._undo()

    def _handle_redo(self, event):
        if hasattr(self.editor, "_redo"):
            self.editor._redo()
