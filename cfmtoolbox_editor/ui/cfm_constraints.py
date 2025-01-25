import tkinter as tk
from tkinter import ttk


class CFMConstraints:
    def __init__(self, parent, editor):
        self.parent = parent
        self.editor = editor
        self._create_constraints_frame()

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
            command=self.editor.constraint_dialog,
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

    def get_tree(self):
        return self.constraints_tree

    def get_constraints_frame(self):
        return self.constraints_frame
