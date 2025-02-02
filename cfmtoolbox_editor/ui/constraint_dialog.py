import tkinter as tk
from tkinter import ttk, messagebox, StringVar

from cfmtoolbox import Constraint

from cfmtoolbox_editor.utils.cfm_utils import (
    edit_str_to_cardinality,
    cardinality_to_edit_str,
)


class ConstraintDialog:
    def __init__(
            self,
            parent,
            editor,
            constraint=None,
            initial_first_feature=None,
            initial_second_feature=None,
    ):
        self.parent = parent
        self.editor = editor
        self.constraint = constraint
        self.initial_first_feature = initial_first_feature
        self.initial_second_feature = initial_second_feature
        self.result = None

        # Initialize instance attributes
        self.dialog = None
        self.first_feature_var = StringVar()
        self.first_card_var = StringVar()
        self.type_var = StringVar(value="requires")
        self.second_feature_var = StringVar()
        self.second_card_var = StringVar()
        self.first_feature_dropdown = None
        self.second_feature_dropdown = None
        self.type_dropdown = None

        # Set up the dialog
        self.setup_dialog()

    def setup_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Edit Constraint" if self.constraint else "Add Constraint")
        self.dialog.geometry("750x100")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        self.create_widgets()
        self.populate_initial_values()

    def create_widgets(self):
        feature_names = [feature.name for feature in self.editor.cfm.features]
        feature_names.sort(key=str.casefold)

        self.first_feature_var = StringVar()
        self.first_card_var = StringVar()
        self.type_var = StringVar(value="requires")
        self.second_feature_var = StringVar()
        self.second_card_var = StringVar()

        tk.Label(self.dialog, text="First Feature:").grid(
            row=0, column=0, padx=5, sticky="w"
        )
        self.first_feature_dropdown = ttk.Combobox(
            self.dialog,
            textvariable=self.first_feature_var,
            values=feature_names,
            state="readonly",
        )
        self.first_feature_dropdown.grid(row=1, column=0, padx=5)

        tk.Label(self.dialog, text="Cardinality:").grid(
            row=0, column=1, padx=5, sticky="w"
        )
        tk.Entry(self.dialog, textvariable=self.first_card_var).grid(
            row=1, column=1, padx=5
        )

        tk.Label(self.dialog, text="Constraint Type:").grid(
            row=0, column=2, padx=5, sticky="w"
        )
        self.type_dropdown = ttk.Combobox(
            self.dialog,
            textvariable=self.type_var,
            values=["requires", "excludes"],
            state="readonly",
        )
        self.type_dropdown.grid(row=1, column=2, padx=5)

        tk.Label(self.dialog, text="Second Feature:").grid(
            row=0, column=3, padx=5, sticky="w"
        )
        self.second_feature_dropdown = ttk.Combobox(
            self.dialog,
            textvariable=self.second_feature_var,
            values=feature_names,
            state="readonly",
        )
        self.second_feature_dropdown.grid(row=1, column=3, padx=5)

        tk.Label(self.dialog, text="Cardinality:").grid(
            row=0, column=4, padx=5, sticky="w"
        )
        tk.Entry(self.dialog, textvariable=self.second_card_var).grid(
            row=1, column=4, padx=5
        )

        tk.Button(self.dialog, text="Save", command=self.on_submit).grid(
            row=2, column=2, pady=10
        )

    def populate_initial_values(self):
        if self.constraint:
            self.first_feature_var.set(self.constraint.first_feature.name)
            self.second_feature_var.set(self.constraint.second_feature.name)
            self.first_card_var.set(
                cardinality_to_edit_str(self.constraint.first_cardinality)
            )
            self.second_card_var.set(
                cardinality_to_edit_str(self.constraint.second_cardinality)
            )
            self.type_var.set("requires" if self.constraint.require else "excludes")
        else:
            self.first_feature_var.set(
                self.initial_first_feature.name if self.initial_first_feature else ""
            )
            self.second_feature_var.set(
                self.initial_second_feature.name if self.initial_second_feature else ""
            )

    def on_submit(self):
        selected_first_feature = self.first_feature_var.get().strip()
        selected_second_feature = self.second_feature_var.get().strip()
        if not selected_first_feature or not selected_second_feature:
            messagebox.showerror("Input Error", "Both features must be selected.")
            return

        first_feature = self.editor.get_feature_by_name(selected_first_feature)
        second_feature = self.editor.get_feature_by_name(selected_second_feature)
        if first_feature == second_feature:
            messagebox.showerror(
                "Input Error", "The first and second features cannot be the same."
            )
            return

        try:
            first_card = edit_str_to_cardinality(self.first_card_var.get().strip())
            second_card = edit_str_to_cardinality(self.second_card_var.get().strip())
        except ValueError:
            messagebox.showerror("Input Error", "Invalid cardinality format.")
            return

        require = self.type_var.get() == "requires"

        if self.constraint:
            self.constraint.first_feature = first_feature
            self.constraint.second_feature = second_feature
            self.constraint.first_cardinality = first_card
            self.constraint.second_cardinality = second_card
            self.constraint.require = require
        else:
            self.result = Constraint(
                require=require,
                first_feature=first_feature,
                first_cardinality=first_card,
                second_feature=second_feature,
                second_cardinality=second_card,
            )
        self.dialog.destroy()

    def show(self):
        self.dialog.wait_window()
        return self.result
