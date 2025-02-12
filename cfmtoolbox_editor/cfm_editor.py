"""
This module defines the CFMEditorApp class, which is responsible for managing the feature model editor
using the Tkinter library. The CFMEditorApp class provides functionalities to add, edit, delete features,
manage constraints, and handle undo/redo operations.

Classes:
    CFMEditorApp: A class to create and manage the feature model editor application.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from cfmtoolbox import Feature, CFM

from cfmtoolbox_editor.ui.cfm_canvas import CFMCanvas
from cfmtoolbox_editor.ui.delete_feature_dialog import DeleteFeatureDialog
from cfmtoolbox_editor.ui.feature_dialog import FeatureDialog

from cfmtoolbox_editor.utils.cfm_shortcuts import ShortcutManager
from cfmtoolbox_editor.utils.cfm_editor_undo_redo import UndoRedoManager
from cfmtoolbox_editor.utils.cfm_click_handler import CFMClickHandler

from cfmtoolbox_editor.ui.cfm_menubar import CFMMenuBar
from cfmtoolbox_editor.ui.cfm_constraints import CFMConstraints


class CFMEditorApp:
    def __init__(self):
        """
        Initialize the CFMEditorApp with the necessary components and UI setup.
        """
        self.cfm = None
        self.root = tk.Tk()
        self.root.title("CFM Editor")

        self.undo_redo_manager = UndoRedoManager()
        self.shortcut_manager = ShortcutManager(self)

        self.click_handler = CFMClickHandler()

        self.CARDINALITY_FONT = ("Arial", 8)

        self._setup_ui()

    def start(self, cfm: CFM) -> CFM:
        """
        Start the editor application with the given feature model.

        Args:
            cfm (CFM): The feature model to edit.

        Returns:
            CFM: The edited feature model.
        """
        self.cfm = cfm
        self.undo_redo_manager.set_initial_state(self.cfm)
        self.canvas.initialize()
        self.update_model_state()
        self.root.mainloop()
        return self.cfm

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, width=800, height=600)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Menu Bar
        self.menubar = CFMMenuBar(self.root, self)
        self.root.config(menu=self.menubar.get_menubar())

        # Constraints
        self.constraints = CFMConstraints(main_frame, self, self.click_handler)

        # Canvas (for model graph)
        self.canvas = CFMCanvas(main_frame, self.root, self, self.click_handler)

        # TODO: is that necessary?
        # Update the shortcut manager with the new editor instance
        self.shortcut_manager.update_editor(self)

    def _exit_application(self):
        self.root.quit()

    def _confirm_save_changes(self):
        return tk.messagebox.askokcancel("Save", "Do you want to save changes?")

    def save_model(self):
        """
        Save the current state of the feature model.
        """
        if self._confirm_save_changes():
            self.root.quit()

    def reset_model(self):
        """
        Reset the feature model to its initial state.
        """
        original_state = self.undo_redo_manager.reset()
        if original_state:
            self._load_state(original_state)

    def undo(self):
        """
        Undo the last action.
        """
        previous_state = self.undo_redo_manager.undo()
        if previous_state:
            self._load_state(previous_state)

    def redo(self):
        """
        Redo the last undone action.
        """
        next_state = self.undo_redo_manager.redo()
        if next_state:
            self._load_state(next_state)

    def _load_state(self, state: CFM):
        self.cfm = state
        self.canvas.initialize_feature_states(self.cfm.root)
        self.canvas.draw_model()
        self.update_constraints()

    def update_model_state(self):
        """
        Update the model state after any change.
        """
        self.canvas.cancel_add_constraint()
        self.undo_redo_manager.add_state(self.cfm)
        self.canvas.draw_model()
        self.update_constraints()

    def add_constraint(self, feature):
        """
        Start the process of adding a constraint between features.

        Args:
            feature (Feature): The feature to start the constraint from.
        """
        self.canvas.add_constraint(feature)

    def update_constraints(self):
        """
        Update the constraints displayed in the treeview.
        """
        self.constraints.update_constraints(self.cfm.constraints)

    def delete_constraint(self, constraint):
        """
        Delete a constraint from the feature model.

        Args:
            constraint (Constraint): The constraint to delete.
        """
        if not messagebox.askokcancel(
            "Delete Constraint",
            f"Are you sure you want to delete the constraint between "
            f"{constraint.first_feature.name} and {constraint.second_feature.name}?",
        ):
            return
        self.cfm.constraints.remove(constraint)
        self.update_model_state()

    def add_feature(self, parent):
        """
        Add a new feature to the feature model.

        Args:
            parent (Feature): The parent feature to add the new feature to.
        """
        self.show_feature_dialog(parent=parent)

    def edit_feature(self, feature):
        """
        Edit an existing feature in the feature model.

        Args:
            feature (Feature): The feature to edit.
        """
        self.show_feature_dialog(feature=feature)

    def delete_feature(self, feature):
        """
        Delete a feature from the feature model.

        Args:
            feature (Feature): The feature to delete.
        """
        # root
        if feature == self.cfm.root:
            messagebox.showerror("Error", "Cannot delete root feature.")

        # leaf
        elif len(feature.children) == 0:
            if messagebox.askokcancel(
                "Delete Feature",
                f"Are you sure you want to delete the feature {feature.name} and related constraints?",
            ):
                feature.parent.children.remove(feature)
                self.cfm.constraints = [
                    c
                    for c in self.cfm.constraints
                    if c.first_feature != feature and c.second_feature != feature
                ]
                self.update_model_state()

        # inner node
        else:
            self.show_delete_dialog(feature)

    def show_delete_dialog(self, feature: Feature):
        """
        Show the dialog for deleting a feature.

        Args:
            feature (Feature): The feature to delete.
        """
        DeleteFeatureDialog(
            parent_widget=self.root,  # Pass the parent widget (e.g., the root window)
            feature=feature,  # The feature to be deleted
            cfm=self.cfm,  # The CFM model containing constraints and features
            update_model_state_callback=self.update_model_state,  # Callback to update the model state
            show_feature_dialog_callback=self.show_feature_dialog,  # Callback to open the feature dialog
        )

    def show_feature_dialog(
        self, parent: Feature | None = None, feature: Feature | None = None
    ):
        """
        Show the dialog for adding or editing a feature.

        Args:
            parent (Feature, optional): The parent feature for the new feature. Defaults to None.
            feature (Feature, optional): The feature being edited. Defaults to None.
        """
        FeatureDialog(
            parent_widget=self.root,
            cfm=self.cfm,
            add_expanded_feature_callback=self.add_expanded_feature,
            update_model_state_callback=self.update_model_state,
            show_feature_dialog_callback=self.show_feature_dialog,
            parent_feature=parent,
            feature=feature,
        )

    def add_expanded_feature(self, feature: Feature):
        """
        Mark a feature as expanded.

        Args:
            feature (Feature): The feature to mark as expanded.
        """
        self.canvas.add_expanded_feature(feature)

    def get_currently_highlighted_feature(self) -> Feature | None:
        """
        Get the currently highlighted feature.

        Returns:
            Feature | None: The currently highlighted feature, or None if no feature is highlighted.
        """
        return self.canvas.currently_highlighted_feature

    def get_feature_by_name(self, name: str) -> Feature | None:
        """
        Get a feature by its name.

        Args:
            name (str): The name of the feature.

        Returns:
            Feature | None: The feature with the specified name, or None if no such feature exists.
        """
        for feature in self.cfm.features:
            if feature.name == name:
                return feature
        return None
