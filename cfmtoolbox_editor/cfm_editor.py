from math import atan2, degrees
import tkinter as tk
from tkinter import ttk
from tkinter import Menu, Toplevel, Label, Entry, Button, StringVar, messagebox
from tkinter.font import Font
from typing import Dict

from cfmtoolbox import Cardinality, Interval, Feature, CFM

from cfmtoolbox_editor.utils.cfm_calc_graph_Layout import GraphLayoutCalculator, Point
from cfmtoolbox_editor.utils.cfm_utils import (
    cardinality_to_display_str,
    edit_str_to_cardinality,
    cardinality_to_edit_str,
    derive_parent_group_cards_for_one_child,
    derive_parent_group_cards_for_multiple_children,
)

from cfmtoolbox_editor.utils.cfm_shortcuts import ShortcutManager
from cfmtoolbox_editor.utils.cfm_editor_undo_redo import UndoRedoManager
from cfmtoolbox_editor.utils.cfm_click_handler import CFMClickHandler

from cfmtoolbox_editor.ui.cfm_menubar import CFMMenuBar
from cfmtoolbox_editor.ui.cfm_constraints import CFMConstraints


class CFMEditorApp:
    def __init__(self):
        self.cfm = None
        self.root = tk.Tk()
        self.root.title("CFM Editor")

        self.undo_redo_manager = UndoRedoManager()
        self.shortcut_manager = ShortcutManager(self)

        self.expanded_features: Dict[
            int, bool
        ] = {}  # Dictionary to track expanded/collapsed state of features
        self.positions: Dict[int, Point] = {}

        self.info_label = None
        self.cancel_button_window = None
        self.currently_highlighted_feature = None

        self.click_handler = CFMClickHandler()

        self._setup_ui()

    def start(self, cfm: CFM) -> CFM:
        self.cfm = cfm
        self.undo_redo_manager.set_initial_state(self.cfm)
        self._initialize_feature_states(self.cfm.root)
        self._update_model_state()
        self.root.mainloop()
        return self.cfm

    def _initialize_feature_states(self, feature):
        # Initialize all features as expanded
        self.expanded_features[id(feature)] = True
        for child in feature.children:
            self._initialize_feature_states(child)

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, width=800, height=600)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Create Menu Bar
        self.menubar = CFMMenuBar(self.root, self)
        self.root.config(menu=self.menubar.get_menubar())

        # Constraints
        self.constraints = CFMConstraints(main_frame, self, self.click_handler)

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
        original_state = self.undo_redo_manager.reset()
        if original_state:
            self._load_state(original_state)

    def _undo(self):
        previous_state = self.undo_redo_manager.undo()
        if previous_state:
            self._load_state(previous_state)

    def _redo(self):
        next_state = self.undo_redo_manager.redo()
        if next_state:
            self._load_state(next_state)

    def _load_state(self, state: CFM):
        self.cfm = state
        self._initialize_feature_states(self.cfm.root)
        self._draw_model()
        self.update_constraints()

    def _update_model_state(self):
        # Call after every change
        self.undo_redo_manager.add_state(self.cfm)
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

    def draw_feature(self, feature: Feature, feature_instance_card_pos: str):
        x, y = self.positions[id(feature)].x, self.positions[id(feature)].y
        node_id, padded_bbox = self._draw_node(feature, x, y)

        if not feature == self.cfm.root:
            self._draw_feat_instance_card(feature, feature_instance_card_pos, padded_bbox, x)

        if feature.children:
            self._draw_collapse_expand_button(feature, padded_bbox, y)

        self.canvas.tag_bind(
            node_id,
            self.click_handler.right_click(),
            lambda event, f=feature: self.on_right_click_node(event, f),
        )

        self.canvas.tag_bind(
            node_id,
            self.click_handler.left_click(),
            lambda event, f=feature: self.on_left_click_node(event, f),
        )

        # Recursively draw children if expanded
        if feature.children and self.expanded_features.get(id(feature), True):
            # arc for group
            arc_radius = 25
            x_center = x
            y_center = y + 10
            left_angle = 180.0
            right_angle = 360.0

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

                    self._draw_group_instance_card(feature, new_x, new_y, padded_bbox, x, y)

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
                self._draw_group_type_card(feature, padded_bbox, x)

    def _draw_node(self, feature, x, y):
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
        return node_id, padded_bbox

    def _draw_feat_instance_card(self, feature, feature_instance_card_pos, padded_bbox, x):
        # bbox[1] is the y-coordinate of the top side of the box
        anchor: str
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

    def _draw_collapse_expand_button(self, feature, padded_bbox, y):
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
        self.canvas.tag_bind(
            button_id,
            self.click_handler.left_click(),
            lambda event, f=feature: self.toggle_children(event, f),
        )

    def _draw_group_instance_card(self, feature, new_x, new_y, padded_bbox, x, y):
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

    def _draw_group_type_card(self, feature, padded_bbox, x):
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
        self.constraints.update_constraints(self.cfm.constraints)

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
            self.constraints.constraint_dialog(
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
        self.canvas.bind(self.click_handler.left_click(), on_canvas_click)

    def cancel_add_constraint(self):
        self.canvas.delete(self.info_label)
        self.canvas.delete(self.cancel_button_window)
        self.canvas.unbind(self.click_handler.left_click())
        if self.currently_highlighted_feature:
            feature_node = self.canvas.find_withtag(
                f"feature_rect:{self.currently_highlighted_feature.name}"
            )
            if feature_node:
                self.canvas.itemconfig(feature_node[0], fill="lightgrey")
            self.currently_highlighted_feature = None

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

    def on_left_click_node(self, event, feature):
        if self.currently_highlighted_feature:
            previous_node = self.canvas.find_withtag(
                f"feature_rect:{self.currently_highlighted_feature.name}"
            )
            if previous_node:
                self.canvas.itemconfig(previous_node[0], fill="lightgrey")

        node_id = self.canvas.find_withtag(f"feature_rect:{feature.name}")
        if node_id:
            self.canvas.itemconfig(node_id[0], fill="lightblue")
            self.currently_highlighted_feature = feature

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
            if not parent:
                messagebox.showerror("Error", "Cannot delete root feature.")
                dialog.destroy()
                return
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
    def show_feature_dialog(
        self, parent: Feature | None = None, feature: Feature | None = None
    ):
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
        is_group = feature is not None and len(feature.children) > 1
        is_only_child = (
            feature is not None and feature.parent and len(feature.parent.children) == 1
        )

        current_name = feature.name if feature is not None else ""
        current_feature_card = (
            cardinality_to_edit_str(feature.instance_cardinality)
            if feature is not None
            else ""
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

        if is_group and feature is not None:
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
