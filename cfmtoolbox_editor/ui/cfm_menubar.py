from tkinter import Menu, messagebox


class CFMMenuBar:
    def __init__(self, root, editor):
        self.root = root
        self.editor = editor
        self.menubar = Menu(root)
        self.shortcut_manager = editor.shortcut_manager
        self._create_menus()

    def _create_menus(self):
        self._create_file_menu()
        self._create_edit_menu()

    def _create_file_menu(self):
        file_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        self._add_menu_command(file_menu, "Save", self.editor.save_model, "SAVE")
        self._add_menu_command(file_menu, "Reset", self.editor.reset_model, "RESET")
        return file_menu

    def _create_edit_menu(self):
        edit_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)
        self._add_menu_command(edit_menu, "Undo", self.editor.undo, "UNDO")
        self._add_menu_command(edit_menu, "Redo", self.editor.redo, "REDO")
        edit_menu.add_separator()
        self._add_menu_command(
            edit_menu,
            "Add Feature",
            lambda: self.editor.add_feature(
                self.editor.get_currently_highlighted_feature()
            ),
            "ADD_FEATURE",
        )
        self._add_menu_command(
            edit_menu,
            "Add Constraint",
            lambda: self.editor.add_constraint(
                self.editor.get_currently_highlighted_feature()
            ),
            "ADD_CONSTRAINT",
        )
        self._add_menu_command(
            edit_menu,
            "Edit Feature",
            lambda: self.editor.edit_feature(
                self.editor.get_currently_highlighted_feature()
            ),
            "EDIT_FEATURE",
        )
        self._add_menu_command(
            edit_menu,
            "Delete Feature",
            lambda: self.editor.delete_feature(
                self.editor.get_currently_highlighted_feature()
            ),
            "DELETE_FEATURE",
        )
        return edit_menu

    def _add_menu_command(self, menu, label, command_func, shortcut_key=None):
        NO_FEATURE_REQUIRED = ["Save", "Reset", "Undo", "Redo"]

        def wrapped_command():
            if (
                self.editor.get_currently_highlighted_feature()
                or label in NO_FEATURE_REQUIRED
            ):
                command_func()
            else:
                messagebox.showerror("Error", "No feature selected.")

        menu.add_command(
            label=label,
            command=wrapped_command,
            accelerator=self.shortcut_manager.accelerators[shortcut_key]
            if shortcut_key
            else None,
        )

    def get_menubar(self):
        return self.menubar
