from math import atan2, degrees
import tkinter as tk
from tkinter import ttk
from copy import deepcopy
from tkinter import Menu, Toplevel, Label, Entry, Button, StringVar, messagebox
from tkinter.font import Font

from cfmtoolbox import Cardinality, Interval, Feature, CFM, Constraint

from cfmtoolbox_editor.calc_graph_Layout import GraphLayoutCalculator, Point
from cfmtoolbox_editor.tooltip import ToolTip
from cfmtoolbox_editor.utils import (
    cardinality_to_display_str,
    edit_str_to_cardinality,
    cardinality_to_edit_str,
    derive_parent_group_cards_for_one_child,
    derive_parent_group_cards_for_multiple_children,
)

from cfmtoolbox_editor.shortcuts import ShortcutManager
from cfmtoolbox_editor.cfm_editor_undo_redo import UndoRedoManager


class CFMEditorApp:
    def __init__(self):
        self.cfm = None
        self.original_cfm = None
        self.root = tk.Tk()
        self.root.title("CFM Editor")

        self.undo_redo = UndoRedoManager()
        self.shortcut_manager = ShortcutManager(self)

        self.expanded_features: dict[
            int, bool
        ] = {}  # Dictionary to track expanded/collapsed state of features
        self.positions: dict[int, Point] = {}

        self.last_hovered_cell = (None, None)  # (row, column) for constraints tooltip
        self.constraint_mapping = {}  # Mapping of constraint treeview items to constraints

        self.info_label = None
        self.cancel_button_window = None
        self.currently_highlighted_feature = None

        self._setup_ui()

    def start(self, cfm) -> CFM:
        self.cfm = cfm
        # Make a deep copy of the CFM to be able to undo changes
        self.original_cfm = deepcopy(cfm)
        self._initialize_feature_states(self.cfm.root)
        self._update_model_state()
        self.root.mainloop()
        return self.cfm

    def _initialize_feature_states(self, feature):
        self.expanded_features[id(feature)] = (
            True  # Initialize all features as expanded
        )
        for child in feature.children:
            self._initialize_feature_states(child)

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, width=800, height=600)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Create Menu Bar
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        # Edit Menu
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(
            label="Undo",
            command=self._undo,
            accelerator=self.shortcut_manager.accelerators["UNDO"],
        )
        edit_menu.add_command(
            label="Redo",
            command=self._redo,
            accelerator=self.shortcut_manager.accelerators["REDO"],
        )

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, pady=5)

        self.save_button = ttk.Button(
            button_frame, text="Save", command=self._save_model
        )
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.reset_button = ttk.Button(
            button_frame, text="Reset", command=self._reset_model
        )
        self.reset_button.pack(side=tk.LEFT, padx=5)

        # Constraints
        constraints_frame = ttk.Frame(main_frame)
        constraints_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        constraints_label = ttk.Label(
            constraints_frame, text="Constraints", font=("Arial", 12, "bold")
        )
        constraints_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        add_constraint_button = ttk.Button(
            constraints_frame, text="Add constraint", command=self.constraint_dialog
        )
        add_constraint_button.grid(row=0, column=1, padx=10, pady=5, sticky="e")

        self.constraints_scroll = ttk.Scrollbar(constraints_frame, orient=tk.VERTICAL)
        self.constraints_scroll.grid(row=1, column=2, sticky="ns")

        self.constraints_tree = ttk.Treeview(
            constraints_frame,
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
        self.constraints_tree.column("First Feature", anchor=tk.E, width=120)
        self.constraints_tree.column("First Cardinality", anchor=tk.W, width=100)
        self.constraints_tree.column("Type", anchor=tk.CENTER, width=60)
        self.constraints_tree.column("Second Feature", anchor=tk.E, width=120)
        self.constraints_tree.column("Second Cardinality", anchor=tk.W, width=100)
        self.constraints_tree.column("Edit", anchor=tk.CENTER, width=50)
        self.constraints_tree.column("Delete", anchor=tk.CENTER, width=50)
        self.constraints_tree.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5)

        self.constraints_tree.config(yscrollcommand=self.constraints_scroll.set)
        self.constraints_scroll.config(command=self.constraints_tree.yview)

        constraints_frame.columnconfigure(0, weight=1)
        constraints_frame.columnconfigure(1, weight=0)
        constraints_frame.rowconfigure(1, weight=1)

        self.constraints_tree.bind("<Button-1>", self.on_constraints_click)

        self.constraints_tooltip = ToolTip(constraints_frame)
        self.constraints_tree.bind("<Motion>", self.on_constraints_hover)
        self.constraints_tree.bind("<Leave>", self.on_constraints_leave)

        # Scrollbars
        self.v_scroll = ttk.Scrollbar(main_frame, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.root.update()
        self.h_scroll = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X, padx=self.v_scroll.winfo_width())

        # Canvas (for model graph)
        self.canvas = tk.Canvas(
            main_frame,
            bg="white",
            width=800,
            height=400,
            scrollregion=(0, 0, 1000, 1000),
        )
        self.canvas.config(
            yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set
        )
        self.canvas.pack(expand=True, fill=tk.BOTH)

        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        # Update the shortcut manager with the new editor instance
        self.shortcut_manager.update_editor(self)

    def _exit_application(self):
        self.root.quit()

    def _confirm_save_changes(self):
        return tk.messagebox.askokcancel("Save", "Do you want to save changes?")

    def _save_model(self):
        if self._confirm_save_changes():
            self.root.quit()

    def _reset_model(self):
        self.cfm = deepcopy(self.original_cfm)
        self._initialize_feature_states(self.cfm.root)
        self._update_model_state()

    def _undo(self):
        previous_state = self.undo_redo.undo()
        if previous_state:
            self.cfm = previous_state
            self._initialize_feature_states(self.cfm.root)
            self._draw_model()
            self.update_constraints()

    def _redo(self):
        next_state = self.undo_redo.redo()
        if next_state:
            self.cfm = next_state
            self._initialize_feature_states(self.cfm.root)
            self._draw_model()
            self.update_constraints()

    def _update_model_state(self):
        # Nach jeder Änderung aufrufen
        self.undo_redo.add_state(self.cfm)
        self._draw_model()
        self.update_constraints()

    def _draw_model(self):
        self.positions = GraphLayoutCalculator(
            self.cfm, self.expanded_features
        ).compute_positions()
        self.canvas.delete("all")
        self.draw_feature(self.cfm.root, "middle")

        # TODO: Does not take into account the sizes of the outermost nodes. Could be solved by a maximum node size.
        min_x = min(pos.x for pos in self.positions.values())
        max_x = max(pos.x for pos in self.positions.values())
        max_y = max(pos.y for pos in self.positions.values())

        padding_x = 100
        padding_y = 50
        self.canvas.config(
            scrollregion=(
                min(min_x - padding_x, 0),
                0,
                max_x + padding_x,
                max_y + padding_y,
            )
        )

    # TODO: Refactor this method as it became too long
    def draw_feature(self, feature: Feature, feature_instance_card_pos: str):
        x, y = self.positions[id(feature)].x, self.positions[id(feature)].y
        node_id = self.canvas.create_text(
            x, y, text=feature.name, tags=(f"feature_text:{feature.name}", feature.name)
        )
        bbox = self.canvas.bbox(node_id)
        padding_x = 4
        padding_y = 2
        padded_bbox = (
            bbox[0] - padding_x,
            bbox[1] - padding_y,
            bbox[2] + padding_x,
            bbox[3] + padding_y,
        )
        rect_id = self.canvas.create_rectangle(
            padded_bbox,
            fill="lightgrey",
            tags=(f"feature_rect:{feature.name}", feature.name),
        )
        self.canvas.tag_raise(node_id, rect_id)

        if not feature == self.cfm.root:
            # bbox[1] is the y-coordinate of the top side of the box
            match feature_instance_card_pos:
                case "right":
                    anchor = tk.W
                    feature_instance_x = x + 4
                case "left":
                    anchor = tk.E
                    feature_instance_x = x - 4
                case _:
                    anchor = tk.CENTER
                    feature_instance_x = x

            feature_instance_y = padded_bbox[1] - 10
            # TODO: The brackets don't look nice
            self.canvas.create_text(
                feature_instance_x,
                feature_instance_y,
                text=cardinality_to_display_str(feature.instance_cardinality, "<", ">"),
                tags=f"{feature.name}_feature_instance",
                anchor=anchor,
            )

        # Add collapse/expand button
        if feature.children:
            expanded = self.expanded_features.get(id(feature), True)
            # TODO: Maybe add colors
            button_text = "-" if expanded else "+"
            button_id = self.canvas.create_text(
                padded_bbox[2] + 10,
                y,
                text=button_text,
                tags="button",
                font=Font(weight="bold"),
            )
            # Button-1 is left mouse button
            self.canvas.tag_bind(
                button_id,
                "<Button-1>",
                lambda event, f=feature: self.toggle_children(event, f),
            )

        # Click event handling (Button-1 is left mouse button, Button-3 is right mouse button)
        self.canvas.tag_bind(
            node_id,
            "<Button-3>",
            lambda event, f=feature: self.on_right_click_node(event, f),
        )

        # Recursively draw children if expanded
        if feature.children and self.expanded_features.get(id(feature), True):
            # arc for group
            arc_radius = 25
            x_center = x
            y_center = y + 10
            left_angle = 180
            right_angle = 360

            for i, child in enumerate(feature.children):
                new_x = self.positions[id(child)].x
                new_y = self.positions[id(child)].y
                self.canvas.create_line(
                    x, y + 10, new_x, new_y - 10, tags="edge", arrow=tk.LAST
                )

                # Calculate angles for the group arc and adjust to canvas coordinate system
                if i == 0:
                    left_angle = (
                        degrees(atan2((new_y - y_center), (new_x - x_center))) + 180
                    ) % 360
                if (i == len(feature.children) - 1) and (len(feature.children) > 1):
                    right_angle = (
                        degrees(atan2((new_y - y_center), (new_x - x_center))) + 180
                    ) % 360

                    # Calculate text position for group instance cardinality with linear interpolation
                    slope = (new_x - x) / (new_y - 10 - (y + 10))
                    group_instance_y = padded_bbox[3] + 10
                    group_instance_x = x + slope * (group_instance_y - (y + 10)) + 5
                    # anchor w means west, so the left side of the text is placed at the specified position
                    self.canvas.create_text(
                        group_instance_x,
                        group_instance_y,
                        text=cardinality_to_display_str(
                            feature.group_instance_cardinality, "<", ">"
                        ),
                        tags=f"{feature.name}_group_instance",
                        anchor=tk.W,
                    )

                child_feature_instance_card_pos = "right" if new_x >= x else "left"
                self.draw_feature(child, child_feature_instance_card_pos)

            if len(feature.children) > 1:
                self.canvas.create_arc(
                    x_center - arc_radius,
                    y_center - arc_radius,
                    x_center + arc_radius,
                    y_center + arc_radius,
                    fill="white",
                    style=tk.PIESLICE,
                    tags="arc",
                    start=left_angle,
                    extent=right_angle - left_angle,
                )
                # bbox[3] is the y-coordinate of the bottom of the text box
                group_type_y = padded_bbox[3] + 10
                self.canvas.create_text(
                    x,
                    group_type_y,
                    text=cardinality_to_display_str(
                        feature.group_type_cardinality, "[", "]"
                    ),
                    tags=f"{feature.name}_group_type",
                )

    def update_constraints(self):
        # delete old entries
        for constraint in self.constraints_tree.get_children():
            self.constraints_tree.delete(constraint)
        self.constraint_mapping = {}

        # add current constraints
        for constraint in self.cfm.constraints:
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
                self.delete_constraint(constraint)

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
                self.constraints_tooltip.hide_tip()
                return

            value = self.constraints_tree.item(item, "values")
            if value and col_index < len(value):
                self.constraints_tooltip.show_tip(value[col_index])
            else:
                self.constraints_tooltip.hide_tip()
        else:
            self.constraints_tooltip.hide_tip()
            self.last_hovered_cell = (None, None)

    def on_constraints_leave(self, event):
        self.constraints_tooltip.hide_tip()
        self.last_hovered_cell = (None, None)

    def constraint_dialog(
        self, constraint=None, initial_first_feature=None, initial_second_feature=None
    ):
        """
        Opens a dialog for adding or editing a constraint. If `constraint` is provided, it will edit the existing
        constraint. Otherwise, it will create a new constraint with `first_feature` and `second_feature` preselected
        if provided.
        """

        def on_submit():
            selected_first_feature = first_feature_var.get().strip()
            selected_second_feature = second_feature_var.get().strip()
            if not selected_first_feature or not selected_second_feature:
                messagebox.showerror("Input Error", "Both features must be selected.")
                return
            first_feature = self.get_feature_by_name(selected_first_feature)
            second_feature = self.get_feature_by_name(selected_second_feature)
            if first_feature == second_feature:
                messagebox.showerror(
                    "Input Error", "The first and second features cannot be the same."
                )
                return

            raw_first_card = first_card_var.get().strip()
            raw_second_card = second_card_var.get().strip()
            first_card = Cardinality([Interval(0, None)])
            second_card = Cardinality([Interval(0, None)])
            if raw_first_card:
                try:
                    first_card = edit_str_to_cardinality(raw_first_card)
                except ValueError:
                    messagebox.showerror(
                        "Input Error",
                        "Invalid cardinality format. Use 'min,max' or 'min,*' for intervals.",
                    )
                    return
            if raw_second_card:
                try:
                    second_card = edit_str_to_cardinality(raw_second_card)
                except ValueError:
                    messagebox.showerror(
                        "Input Error",
                        "Invalid cardinality format. Use 'min,max' or 'min,*' for intervals.",
                    )
                    return

            constraint_type = type_var.get().strip()

            if constraint:
                # Update the existing constraint
                constraint.first_feature = first_feature
                constraint.second_feature = second_feature
                constraint.first_cardinality = first_card
                constraint.second_cardinality = second_card
                constraint.require = constraint_type == "requires"
            else:
                # Create a new constraint
                new_constraint = Constraint(
                    require=(constraint_type == "requires"),
                    first_feature=first_feature,
                    first_cardinality=first_card,
                    second_feature=second_feature,
                    second_cardinality=second_card,
                )
                self.cfm.constraints.append(new_constraint)

            self.update_constraints()
            dialog.destroy()

        # Prepare the dialog
        dialog = tk.Toplevel()
        dialog.title("Edit Constraint" if constraint else "Add Constraint")
        dialog.geometry("750x100")
        dialog.transient(self.root)
        dialog.grab_set()

        feature_names = [feature.name for feature in self.cfm.features]
        feature_names.sort(key=str.casefold)

        if constraint:
            initial_first_card = cardinality_to_edit_str(constraint.first_cardinality)
            initial_second_card = cardinality_to_edit_str(constraint.second_cardinality)
            initial_constraint_type = "requires" if constraint.require else "excludes"
            initial_first_feature = constraint.first_feature.name
            initial_second_feature = constraint.second_feature.name
        else:
            initial_first_card = ""
            initial_second_card = ""
            initial_constraint_type = "requires"
            initial_first_feature = (
                initial_first_feature.name if initial_first_feature else ""
            )
            initial_second_feature = (
                initial_second_feature.name if initial_second_feature else ""
            )

        first_feature_label = tk.Label(dialog, text="First Feature:")
        first_feature_label.grid(row=0, column=0, padx=5, pady=0, sticky="w")
        first_feature_var = StringVar(value=initial_first_feature)
        first_feature_dropdown = ttk.Combobox(
            dialog,
            textvariable=first_feature_var,
            values=feature_names,
            state="readonly",
        )
        first_feature_dropdown.grid(row=1, column=0, padx=5, pady=5)

        first_card_label = tk.Label(dialog, text="Cardinality:")
        first_card_label.grid(row=0, column=1, padx=5, pady=0, sticky="w")
        first_card_var = StringVar(value=initial_first_card)
        first_card_entry = tk.Entry(dialog, textvariable=first_card_var)
        first_card_entry.grid(row=1, column=1, padx=5, pady=5)

        type_label = tk.Label(dialog, text="Constraint Type:")
        type_label.grid(row=0, column=2, padx=5, pady=0, sticky="w")
        type_var = StringVar(value=initial_constraint_type)
        type_dropdown = ttk.Combobox(
            dialog, textvariable=type_var, values=["requires", "excludes"]
        )
        type_dropdown.grid(row=1, column=2, padx=5, pady=5)

        second_feature_label = tk.Label(dialog, text="Second Feature:")
        second_feature_label.grid(row=0, column=3, padx=5, pady=0, sticky="w")
        second_feature_var = StringVar(value=initial_second_feature)
        second_feature_dropdown = ttk.Combobox(
            dialog,
            textvariable=second_feature_var,
            values=feature_names,
            state="readonly",
        )
        second_feature_dropdown.grid(row=1, column=3, padx=5, pady=5)

        second_card_label = tk.Label(dialog, text="Cardinality:")
        second_card_label.grid(row=0, column=4, padx=5, pady=0, sticky="w")
        second_card_var = StringVar(value=initial_second_card)
        second_card_entry = tk.Entry(dialog, textvariable=second_card_var)
        second_card_entry.grid(row=1, column=4, padx=5, pady=5)

        submit_button = tk.Button(dialog, text="Save", command=on_submit)
        submit_button.grid(row=2, column=2, pady=10)

        dialog.wait_window(dialog)

    def add_constraint(self, feature):
        feature_node = self.canvas.find_withtag(f"feature_rect:{feature.name}")
        if feature_node:
            self.canvas.itemconfig(feature_node[0], fill="lightblue")
            self.currently_highlighted_feature = feature

        def on_canvas_click(event):
            clicked_item = self.canvas.find_withtag("current")
            if not clicked_item:
                messagebox.showerror("Selection Error", "Please click on a feature.")
                return

            clicked_tags = self.canvas.gettags(clicked_item[0])
            second_feature_name = next(
                (
                    tag
                    for tag in clicked_tags
                    if tag in (feat.name for feat in self.cfm.features)
                ),
                None,
            )
            second_feature = next(
                (f for f in self.cfm.features if f.name == second_feature_name), None
            )

            if not second_feature:
                messagebox.showerror("Selection Error", "Please click on a feature.")
                return

            self.cancel_add_constraint()
            self.constraint_dialog(
                initial_first_feature=feature, initial_second_feature=second_feature
            )

        self.info_label = self.canvas.create_text(
            400,
            15,
            text="Click on the second feature to define the constraint.",
            fill="black",
            font=("Arial", 12),
        )
        cancel_button = ttk.Button(
            self.root, text="Cancel", command=self.cancel_add_constraint
        )
        self.cancel_button_window = self.canvas.create_window(
            650, 15, window=cancel_button
        )
        self.canvas.bind("<Button-1>", on_canvas_click)

    def cancel_add_constraint(self):
        self.canvas.delete(self.info_label)
        self.canvas.delete(self.cancel_button_window)
        self.canvas.unbind("<Button-1>")
        if self.currently_highlighted_feature:
            feature_node = self.canvas.find_withtag(
                f"feature_rect:{self.currently_highlighted_feature.name}"
            )
            if feature_node:
                self.canvas.itemconfig(feature_node[0], fill="lightgrey")
            self.currently_highlighted_feature = None

    def edit_constraint(self, constraint):
        self.constraint_dialog(constraint=constraint)

    def delete_constraint(self, constraint):
        # Ask user if they are sure
        if not messagebox.askokcancel(
            "Delete Constraint",
            f"Are you sure you want to delete the constraint between "
            f"{constraint.first_feature.name} and {constraint.second_feature.name}?",
        ):
            return
        self.cfm.constraints.remove(constraint)
        self.update_constraints()

    def toggle_children(self, event, feature):
        self.expanded_features[id(feature)] = not self.expanded_features.get(
            id(feature), True
        )
        self._update_model_state()

    def on_right_click_node(self, event, feature):
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="Add Child", command=lambda: self.add_feature(feature))
        menu.add_command(
            label="Edit Feature", command=lambda: self.edit_feature(feature)
        )
        menu.add_command(
            label="Delete Feature", command=lambda: self.delete_feature(feature)
        )
        menu.add_command(
            label="Add Constraint", command=lambda: self.add_constraint(feature)
        )
        menu.post(event.x_root, event.y_root)

    def add_feature(self, parent):
        self.show_feature_dialog(parent=parent)

    def edit_feature(self, feature):
        self.show_feature_dialog(feature=feature)

    def delete_feature(self, feature):
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
                self._update_model_state()

        # inner node
        else:
            self.show_delete_dialog(feature)

    # This is only used for inner nodes, so it is safe to assume that the feature has children and a parent.
    def show_delete_dialog(self, feature: Feature):
        def submit(delete_subtree: bool):
            parent = feature.parent
            former_number_of_children = len(parent.children)
            if delete_subtree:
                # Remove all constraints that contain one of the children of the feature
                self.cfm.constraints = [
                    c
                    for c in self.cfm.constraints
                    if c.first_feature not in feature.children
                    and c.second_feature not in feature.children
                ]
            else:
                # Move its children to the parent at the index of the feature
                index = parent.children.index(feature)
                for child in reversed(feature.children):
                    parent.children.insert(index, child)
                    child.parent = parent
            parent.children.remove(feature)
            self.cfm.constraints = [
                c
                for c in self.cfm.constraints
                if c.first_feature != feature and c.second_feature != feature
            ]
            group_created = False
            if len(parent.children) == 0:
                parent.group_type_cardinality, parent.group_instance_cardinality = (
                    Cardinality([]),
                    Cardinality([]),
                )
            if len(parent.children) == 1:
                parent.group_type_cardinality, parent.group_instance_cardinality = (
                    derive_parent_group_cards_for_one_child(
                        parent.children[0].instance_cardinality
                    )
                )
            # A new group was created
            if len(parent.children) == 2 and former_number_of_children < 2:
                parent.group_type_cardinality, parent.group_instance_cardinality = (
                    derive_parent_group_cards_for_multiple_children(
                        [child.instance_cardinality for child in parent.children]
                    )
                )
                group_created = True

            self._update_model_state()
            dialog.destroy()
            if group_created:
                messagebox.showinfo(
                    "Group Created",
                    "A new group was created. You can edit its cardinalities now.",
                )
                self.show_feature_dialog(feature=parent)

        dialog = tk.Toplevel()
        dialog.title("Delete Method")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()

        label = tk.Label(
            dialog,
            text=(
                f"Choose the delete method for feature {feature.name}. Delete subtree will also delete all descendents, transfer will attach them to their grand-parent."
            ),
            wraplength=280,
            justify="left",
        )
        label.pack(pady=10)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        tk.Button(
            button_frame, text="Delete subtree", command=lambda: submit(True)
        ).pack(side="left", padx=5)
        tk.Button(button_frame, text="Transfer", command=lambda: submit(False)).pack(
            side="left", padx=5
        )
        tk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(
            side="left", padx=5
        )

        dialog.wait_window(dialog)

    # Used for adding and editing features. If feature is None, a new feature is added, otherwise the feature is edited.
    def show_feature_dialog(self, parent: Feature = None, feature: Feature = None):
        def on_submit():
            feature_name = name_var.get().strip()
            if not feature_name:
                messagebox.showerror("Input Error", "Feature name cannot be empty.")
                return
            if (feature_name in [f.name for f in self.cfm.features]) and (
                not is_edit or (feature_name != feature.name)
            ):
                messagebox.showerror("Input Error", "Feature name must be unique.")
                return

            raw_feature_card = feature_card_var.get().strip()
            feature_card = Cardinality([Interval(0, None)])
            if raw_feature_card:
                try:
                    feature_card = edit_str_to_cardinality(raw_feature_card)
                except ValueError:
                    messagebox.showerror(
                        "Input Error",
                        "Invalid feature cardinality format. Use 'min,max' or 'min,*' for intervals.",
                    )
                    return

            group_created = False

            if is_edit:
                feature.name = feature_name
                feature.instance_cardinality = feature_card
                if is_group:
                    raw_group_type_card = group_type_card_var.get().strip()
                    raw_group_instance_card = group_instance_card_var.get().strip()
                    try:
                        group_type_card = edit_str_to_cardinality(raw_group_type_card)
                    except ValueError:
                        messagebox.showerror(
                            "Input Error",
                            "Invalid group type cardinality format. Use 'min,max' or 'min,*' for intervals.",
                        )
                        return
                    try:
                        group_instance_card = edit_str_to_cardinality(
                            raw_group_instance_card
                        )
                    except ValueError:
                        messagebox.showerror(
                            "Input Error",
                            "Invalid group instance cardinality format. Use 'min,max' or 'min,*' for intervals.",
                        )
                        return
                    feature.group_type_cardinality = group_type_card
                    feature.group_instance_cardinality = group_instance_card
                if is_only_child:
                    (
                        feature.parent.group_type_cardinality,
                        feature.parent.group_instance_cardinality,
                    ) = derive_parent_group_cards_for_one_child(
                        feature.instance_cardinality
                    )

            else:
                new_feature = Feature(
                    name=feature_name,
                    instance_cardinality=feature_card,
                    group_type_cardinality=Cardinality([]),
                    group_instance_cardinality=Cardinality([]),
                    parent=parent,
                    children=[],
                )
                self.expanded_features[id(new_feature)] = (
                    True  # Initialize new feature as expanded
                )
                parent.children.append(new_feature)
                if len(parent.children) == 1:
                    parent.group_type_cardinality, parent.group_instance_cardinality = (
                        derive_parent_group_cards_for_one_child(feature_card)
                    )
                if len(parent.children) == 2:
                    group_created = True
                    parent.group_type_cardinality, parent.group_instance_cardinality = (
                        derive_parent_group_cards_for_multiple_children(
                            [child.instance_cardinality for child in parent.children]
                        )
                    )

            self._update_model_state()
            dialog.destroy()
            if group_created:
                messagebox.showinfo(
                    "Group Created",
                    "A new group was created. You can edit its cardinalities now.",
                )
                self.show_feature_dialog(feature=parent)

        dialog = Toplevel(self.root)
        dialog.withdraw()
        dialog.title("Edit Feature" if feature else "Add Feature")

        is_edit = feature is not None
        is_group = is_edit and len(feature.children) > 1
        is_only_child = is_edit and feature.parent and len(feature.parent.children) == 1

        current_name = feature.name if is_edit else ""
        current_feature_card = (
            cardinality_to_edit_str(feature.instance_cardinality) if is_edit else ""
        )

        Label(dialog, text="Feature Name:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        name_var = StringVar(value=current_name)
        Entry(dialog, textvariable=name_var).grid(row=0, column=1, padx=5, pady=5)

        Label(dialog, text="Feature cardinality (e.g., '1,2; 5,*'):").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        feature_card_var = StringVar(value=current_feature_card)
        Entry(dialog, textvariable=feature_card_var).grid(
            row=1, column=1, padx=5, pady=5
        )

        if is_group:
            current_group_type_card = cardinality_to_edit_str(
                feature.group_type_cardinality
            )
            current_group_instance_card = cardinality_to_edit_str(
                feature.group_instance_cardinality
            )

            Label(dialog, text="Group type cardinality:").grid(
                row=2, column=0, padx=5, pady=5, sticky="w"
            )
            group_type_card_var = StringVar(value=current_group_type_card)
            Entry(dialog, textvariable=group_type_card_var).grid(
                row=2, column=1, padx=5, pady=5
            )

            Label(dialog, text="Group instance cardinality:").grid(
                row=3, column=0, padx=5, pady=5, sticky="w"
            )
            group_instance_card_var = StringVar(value=current_group_instance_card)
            Entry(dialog, textvariable=group_instance_card_var).grid(
                row=3, column=1, padx=5, pady=5
            )

        Button(
            dialog, text="Save changes" if is_edit else "Add", command=on_submit
        ).grid(row=4, column=0, columnspan=2, pady=10)

        # Center the dialog window
        self.root.update_idletasks()
        main_window_x = self.root.winfo_x()
        main_window_y = self.root.winfo_y()
        main_window_width = self.root.winfo_width()
        main_window_height = self.root.winfo_height()

        dialog_x = (
            main_window_x + (main_window_width // 2) - (dialog.winfo_reqwidth() // 2)
        )
        dialog_y = (
            main_window_y + (main_window_height // 2) - (dialog.winfo_reqheight() // 2)
        )

        dialog.geometry(f"+{dialog_x}+{dialog_y}")

        dialog.deiconify()
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.wait_window()

    def get_feature_by_name(self, name: str) -> Feature | None:
        for feature in self.cfm.features:
            if feature.name == name:
                return feature
        return None
