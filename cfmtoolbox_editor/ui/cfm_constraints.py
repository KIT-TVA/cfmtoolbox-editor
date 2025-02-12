"""
This module defines the CFMConstraints class, which is responsible for managing and displaying constraints
in a feature model using the Tkinter library. The CFMConstraints class provides functionalities to add, edit,
and delete constraints, as well as to display them in a treeview with tooltips for additional information.

Classes:
    CFMConstraints: A class to create and manage the UI elements for displaying and interacting with constraints.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Tuple, List

from cfmtoolbox import Constraint

from cfmtoolbox_editor.ui.cfm_tooltip import ToolTip
from cfmtoolbox_editor.ui.constraint_dialog import ConstraintDialog
from cfmtoolbox_editor.utils.cfm_utils import cardinality_to_display_str


class CFMConstraints:
    def __init__(self, parent, editor, click_handler):
        self.parent = parent
        self.editor = editor
        self.click_handler = click_handler
        self.constraint_mapping: Dict[
            str, Constraint
        ] = {}  # Mapping of constraint treeview items to constraints
        self.last_hovered_cell: Tuple[str | None, str | None] = (
            None,
            None,
        )  # (row, column) for constraints tooltip
        self._create_constraints_frame()
        self.tooltip = self._create_constraints_tooltip()

    def _create_constraints_frame(self):
        self.constraints_frame = ttk.Frame(self.parent)
        self.constraints_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        # Label
        self.constraints_label = ttk.Label(
            self.constraints_frame, text="Constraints", font=("Arial", 12, "bold")
        )
        self.constraints_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Add Button
        self.add_constraint_button = ttk.Button(
            self.constraints_frame,
            text="Add constraint",
            command=self.constraint_dialog,
        )
        self.add_constraint_button.grid(row=0, column=1, padx=10, pady=5, sticky="e")

        # Scrollbar
        self.constraints_scroll = ttk.Scrollbar(
            self.constraints_frame, orient=tk.VERTICAL
        )
        self.constraints_scroll.grid(row=1, column=2, sticky="ns")

        # Treeview
        self._setup_treeview()

        self.constraints_tree.config(yscrollcommand=self.constraints_scroll.set)
        self.constraints_scroll.config(command=self.constraints_tree.yview)

        self.constraints_frame.columnconfigure(0, weight=1)
        self.constraints_frame.columnconfigure(1, weight=0)
        self.constraints_frame.rowconfigure(1, weight=1)
        self.constraints_tree.bind(
            self.click_handler.left_click(), self.on_constraints_click
        )
        self.constraints_tree.bind("<Motion>", self.on_constraints_hover)
        self.constraints_tree.bind("<Leave>", self.on_constraints_leave)

    def _setup_treeview(self):
        columns_config = {
            "First Feature": (tk.E, 140),
            "First Cardinality": (tk.W, 90),
            "Type": (tk.CENTER, 60),
            "Second Feature": (tk.E, 140),
            "Second Cardinality": (tk.W, 90),
            "Edit": (tk.CENTER, 40),
            "Delete": (tk.CENTER, 40),
        }
        self.constraints_tree = ttk.Treeview(
            self.constraints_frame,
            columns=list(columns_config.keys()),
            show="tree",
            height=4,
        )

        for col, (anchor, width) in columns_config.items():
            self.constraints_tree.column(col, anchor=anchor, width=width)

        # Hide the tree column (used for tree hierarchy and indentation, but not needed when used as a flat list)
        self.constraints_tree.column("#0", width=0, stretch=tk.NO)

        self.constraints_tree.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5)

    def _create_constraints_tooltip(self):
        return ToolTip(self.constraints_frame)

    def get_tree(self):
        """
        Get the treeview widget for displaying constraints.

        Returns:
            ttk.Treeview: The treeview widget.
        """
        return self.constraints_tree

    def get_constraints_frame(self):
        """
        Get the frame containing the constraints UI elements.

        Returns:
            ttk.Frame: The frame containing the constraints UI elements.
        """
        return self.constraints_frame

    def update_constraints(self, constraints: List[Constraint]):
        """
        Update the constraints displayed in the treeview.

        Args:
            constraints (List[Constraint]): The list of constraints to display.
        """
        self.constraints_tree.delete(*self.constraints_tree.get_children())
        self.constraint_mapping = {}
        for constraint in constraints:
            constraint_id = self.constraints_tree.insert(
                "",
                "end",
                values=(
                    constraint.first_feature.name,
                    cardinality_to_display_str(constraint.first_cardinality, "⟨", "⟩"),
                    "requires" if constraint.require else "excludes",
                    constraint.second_feature.name,
                    cardinality_to_display_str(constraint.second_cardinality, "⟨", "⟩"),
                    "🖉",
                    "🗑️",
                ),
            )
            self.constraint_mapping[constraint_id] = constraint

    def on_constraints_click(self, event):
        """
        Handle click events on the constraints treeview.

        Args:
            event (tk.Event): The click event.
        """
        region = self.constraints_tree.identify("region", event.x, event.y)
        if region == "cell":
            row = self.constraints_tree.identify_row(event.y)
            constraint = self.constraint_mapping.get(row)
            if not constraint:
                return

            column = self.constraints_tree.identify_column(event.x)
            col_index = int(column[1:]) - 1
            columns = self.constraints_tree["columns"]
            col_name = columns[col_index] if 0 <= col_index < len(columns) else None

            if col_name == "Edit":
                self.edit_constraint(constraint)

            elif col_name == "Delete":
                self.editor.delete_constraint(constraint)

    def on_constraints_hover(self, event):
        """
        Handle hover events on the constraints treeview to show tooltips.

        Args:
            event (tk.Event): The hover event.
        """
        item = self.constraints_tree.identify_row(event.y)
        column = self.constraints_tree.identify_column(event.x)

        if item and column:
            if (item, column) == self.last_hovered_cell:
                return
            self.last_hovered_cell = (item, column)

            col_index = int(column[1:]) - 1
            columns = self.constraints_tree["columns"]
            col_name = columns[col_index] if 0 <= col_index < len(columns) else None
            if col_name in ["Edit", "Delete", None]:
                self.tooltip.hide_tip()
                return

            value = self.constraints_tree.item(item, "values")
            if value and col_index < len(value):
                self.tooltip.show_tip(value[col_index], x_pos=100)
            else:
                self.tooltip.hide_tip()
        else:
            self.tooltip.hide_tip()
            self.last_hovered_cell = (None, None)

    def on_constraints_leave(self, event):
        """
        Handle leave events on the constraints treeview to hide tooltips.

        Args:
            event (tk.Event): The leave event.
        """
        self.tooltip.hide_tip()
        self.last_hovered_cell = (None, None)

    def edit_constraint(self, constraint):
        """
        Open the dialog to edit an existing constraint.

        Args:
            constraint (Constraint): The constraint to edit.
        """
        self.constraint_dialog(constraint=constraint)

    def constraint_dialog(
        self, constraint=None, initial_first_feature=None, initial_second_feature=None
    ):
        """
        Opens a dialog for adding or editing a constraint. If `constraint` is provided, it will edit the existing
        constraint. Otherwise, it will create a new constraint with `first_feature` and `second_feature` preselected
        if provided.

        Args:
            constraint (Constraint, optional): The constraint to edit. Defaults to None.
            initial_first_feature (Feature, optional): The first feature to preselect. Defaults to None.
            initial_second_feature (Feature, optional): The second feature to preselect. Defaults to None.
        """
        dialog = ConstraintDialog(
            parent_widget=self.editor.root,
            editor=self.editor,
            constraint=constraint,
            initial_first_feature=initial_first_feature,
            initial_second_feature=initial_second_feature,
        )
        result = dialog.show()
        if result:
            self.editor.cfm.constraints.append(result)
        self.editor.update_model_state()
