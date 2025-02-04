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
        self.constraints_tree = ttk.Treeview(
            self.constraints_frame,
            columns=(
                "First Feature",
                "First Cardinality",
                "Type",
                "Second Feature",
                "Second Cardinality",
                "Edit",
                "Delete",
            ),
            show="tree",
            height=4,
        )
        self._setup_tree_columns()
        self.constraints_tree.bind(
            self.click_handler.left_click(), self.on_constraints_click
        )
        self.constraints_tree.bind("<Motion>", self.on_constraints_hover)
        self.constraints_tree.bind("<Leave>", self.on_constraints_leave)

    def _setup_tree_columns(self):
        columns_config = {
            "First Feature": (tk.E, 120),
            "First Cardinality": (tk.W, 100),
            "Type": (tk.CENTER, 60),
            "Second Feature": (tk.E, 120),
            "Second Cardinality": (tk.W, 100),
            "Edit": (tk.CENTER, 50),
            "Delete": (tk.CENTER, 50),
        }

        for col, (anchor, width) in columns_config.items():
            self.constraints_tree.column(col, anchor=anchor, width=width)

        self.constraints_tree.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5)
        self.constraints_tree.config(yscrollcommand=self.constraints_scroll.set)
        self.constraints_scroll.config(command=self.constraints_tree.yview)

        self.constraints_frame.columnconfigure(0, weight=1)
        self.constraints_frame.columnconfigure(1, weight=0)
        self.constraints_frame.rowconfigure(1, weight=1)

    def _create_constraints_tooltip(self):
        return ToolTip(self.constraints_frame)

    def get_tree(self):
        return self.constraints_tree

    def get_constraints_frame(self):
        return self.constraints_frame

    def update_constraints(self, constraints: List[Constraint]):
        self.constraints_tree.delete(*self.constraints_tree.get_children())
        self.constraint_mapping = {}
        for constraint in constraints:
            constraint_id = self.constraints_tree.insert(
                "",
                "end",
                values=(
                    constraint.first_feature.name,
                    cardinality_to_display_str(constraint.first_cardinality, "<", ">"),
                    "requires" if constraint.require else "excludes",
                    constraint.second_feature.name,
                    cardinality_to_display_str(constraint.second_cardinality, "<", ">"),
                    "🖉",
                    "🗑️",
                ),
            )
            self.constraint_mapping[constraint_id] = constraint

    def on_constraints_click(self, event):
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
                # print(f"Edit icon clicked for row {row}")
                self.edit_constraint(constraint)

            elif col_name == "Delete":
                # print(f"Delete icon clicked for row {row}")
                self.editor.delete_constraint(constraint)

    def on_constraints_hover(self, event):
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
                self.tooltip.show_tip(value[col_index])
            else:
                self.tooltip.hide_tip()
        else:
            self.tooltip.hide_tip()
            self.last_hovered_cell = (None, None)

    def on_constraints_leave(self, event):
        self.tooltip.hide_tip()
        self.last_hovered_cell = (None, None)

    def edit_constraint(self, constraint):
        self.constraint_dialog(constraint=constraint)

    def constraint_dialog(
        self, constraint=None, initial_first_feature=None, initial_second_feature=None
    ):
        """
        Opens a dialog for adding or editing a constraint. If `constraint` is provided, it will edit the existing
        constraint. Otherwise, it will create a new constraint with `first_feature` and `second_feature` preselected
        if provided.
        """
        dialog = ConstraintDialog(
            parent=self.editor.root,
            editor=self.editor,
            constraint=constraint,
            initial_first_feature=initial_first_feature,
            initial_second_feature=initial_second_feature,
        )
        result = dialog.show()
        if result:
            self.editor.cfm.constraints.append(result)
        self.update_constraints(self.editor.cfm.constraints)
