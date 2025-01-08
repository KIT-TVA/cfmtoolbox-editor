from math import atan2, degrees
import tkinter as tk
from tkinter import ttk
from copy import deepcopy
from tkinter import Menu, Toplevel, Label, Entry, Button, StringVar, messagebox
from tkinter.font import Font

from cfmtoolbox import Cardinality, Interval, Feature, CFM, Constraint

from cfmtoolbox_editor.calc_graph_Layout import GraphLayoutCalculator
from cfmtoolbox_editor.utils import cardinality_to_display_str, edit_str_to_cardinality, cardinality_to_edit_str, \
    derive_parent_group_cards_for_one_child, derive_parent_group_cards_for_multiple_children


class CFMEditorApp:
    def __init__(self):
        self.cfm = None
        self.original_cfm = None
        self.root = tk.Tk()
        self.root.title("CFM Editor")
        self.expanded_features = {}  # Dictionary to track expanded/collapsed state of features
        self.positions = {}

        self._setup_ui()

    def start(self, cfm) -> CFM:
        self.cfm = cfm
        # Make a deep copy of the CFM to be able to undo changes
        self.original_cfm = deepcopy(cfm)
        self._initialize_feature_states(self.cfm.root)
        self._draw_model()
        self.root.mainloop()
        return self.cfm

    def _initialize_feature_states(self, feature):
        self.expanded_features[id(feature)] = True  # Initialize all features as expanded
        for child in feature.children:
            self._initialize_feature_states(child)

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, width=800, height=600)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, pady=5)

        self.save_button = ttk.Button(button_frame, text="Save", command=self._save_model)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.reset_button = ttk.Button(button_frame, text="Reset", command=self._reset_model)
        self.reset_button.pack(side=tk.LEFT, padx=5)

        # Constraints
        constraints_frame = ttk.Frame(main_frame)
        constraints_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        constraints_label = ttk.Label(constraints_frame, text="Constraints", font=("Arial", 12, "bold"))
        constraints_label.pack(side=tk.TOP, pady=5)

        self.constraints_tree = ttk.Treeview(constraints_frame, columns=(
            "First Feature", "First Cardinality", "Type", "Second Feature", "Second Cardinality", "Edit", "Delete"),
                                             show="tree",
                                             height=6)
        self.constraints_tree.column("First Feature", anchor=tk.W, width=150)
        self.constraints_tree.column("First Cardinality", anchor=tk.W, width=120)
        self.constraints_tree.column("Type", anchor=tk.W, width=100)
        self.constraints_tree.column("Second Feature", anchor=tk.W, width=150)
        self.constraints_tree.column("Second Cardinality", anchor=tk.W, width=120)
        self.constraints_tree.column("Edit", anchor=tk.CENTER, width=50)
        self.constraints_tree.column("Delete", anchor=tk.CENTER, width=50)
        self.constraints_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tree_scroll = ttk.Scrollbar(constraints_frame, orient=tk.VERTICAL, command=self.constraints_tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.constraints_tree.config(yscrollcommand=tree_scroll.set)

        self.constraints_tree.bind("<Button-1>", self.on_constraints_click)

        # TODO: Button to add new constraint (or action on features)

        # Scrollbars
        self.v_scroll = ttk.Scrollbar(main_frame, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.root.update()
        self.h_scroll = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X, padx=self.v_scroll.winfo_width())

        # Canvas (for model graph)
        self.canvas = tk.Canvas(main_frame, bg="white", width=800, height=400, scrollregion=(0, 0, 1000, 1000))
        self.canvas.config(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.canvas.pack(expand=True, fill=tk.BOTH)

        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

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
        self._draw_model()

    # TODO: Calculate more suitable feature positions
    def _draw_model(self):
        self.positions = GraphLayoutCalculator(self.cfm).compute_positions()
        self.canvas.delete("all")
        self.draw_feature(self.cfm.root, "middle")

        min_x = min(pos.x for pos in self.positions.values())
        min_y = min(pos.y for pos in self.positions.values())
        max_x = max(pos.x for pos in self.positions.values())
        max_y = max(pos.y for pos in self.positions.values())

        padding_x = 100
        padding_y = 50
        self.canvas.config(scrollregion=(min_x - padding_x, min_y - padding_y, max_x + padding_x, max_y + padding_y))

        self.update_constraints()

    # TODO: Refactor this method as it became too long
    def draw_feature(self, feature: Feature, feature_instance_card_pos: str):
        x, y = self.positions[id(feature)].x, self.positions[id(feature)].y
        node_id = self.canvas.create_text(x, y, text=feature.name, tags=feature.name)
        bbox = self.canvas.bbox(node_id)
        padding_x = 4
        padding_y = 2
        padded_bbox = (bbox[0] - padding_x, bbox[1] - padding_y, bbox[2] + padding_x, bbox[3] + padding_y)
        rect_id = self.canvas.create_rectangle(padded_bbox, fill="lightgrey")
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
            feature_instance_id = self.canvas.create_text(feature_instance_x, feature_instance_y,
                                                          text=cardinality_to_display_str(feature.instance_cardinality,
                                                                                          "<",
                                                                                          ">"),
                                                          tags=f"{feature.name}_feature_instance", anchor=anchor)

        # Add collapse/expand button
        if feature.children:
            expanded = self.expanded_features.get(id(feature), True)
            # TODO: Maybe add colors
            button_text = "-" if expanded else "+"
            button_id = self.canvas.create_text(padded_bbox[2] + 10, y, text=button_text, tags="button",
                                                font=Font(weight="bold"))
            # Button-1 is left mouse button
            self.canvas.tag_bind(button_id, "<Button-1>", lambda event, f=feature: self.toggle_children(event, f))

        # Click event handling (Button-1 is left mouse button, Button-3 is right mouse button)
        self.canvas.tag_bind(node_id, "<Button-3>", lambda event, f=feature: self.on_right_click_node(event, f))

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
                edge_id = self.canvas.create_line(x, y + 10, new_x, new_y - 10, tags="edge", arrow=tk.LAST)

                # Calculate angles for the group arc and adjust to canvas coordinate system
                if i == 0:
                    left_angle = (degrees(atan2((new_y - y_center), (new_x - x_center))) + 180) % 360
                if (i == len(feature.children) - 1) and (len(feature.children) > 1):
                    right_angle = (degrees(atan2((new_y - y_center), (new_x - x_center))) + 180) % 360

                    # Calculate text position for group instance cardinality with linear interpolation
                    slope = (new_x - x) / (new_y - 10 - (y + 10))
                    group_instance_y = padded_bbox[3] + 10
                    group_instance_x = x + slope * (group_instance_y - (y + 10)) + 5
                    # anchor w means west, so the left side of the text is placed at the specified position
                    self.canvas.create_text(group_instance_x, group_instance_y,
                                            text=cardinality_to_display_str(feature.group_instance_cardinality, "<",
                                                                            ">"),
                                            tags=f"{feature.name}_group_instance", anchor=tk.W)

                child_feature_instance_card_pos = "right" if new_x >= x else "left"
                self.draw_feature(child, child_feature_instance_card_pos)

            if len(feature.children) > 1:
                arc_id = self.canvas.create_arc(x_center - arc_radius, y_center - arc_radius, x_center + arc_radius,
                                                y_center + arc_radius, fill="white", style=tk.PIESLICE, tags="arc",
                                                start=left_angle, extent=right_angle - left_angle)
                # bbox[3] is the y-coordinate of the bottom of the text box
                group_type_y = padded_bbox[3] + 10
                group_type_id = self.canvas.create_text(x, group_type_y,
                                                        text=cardinality_to_display_str(feature.group_type_cardinality,
                                                                                        "[",
                                                                                        "]"),
                                                        tags=f"{feature.name}_group_type")

    def update_constraints(self):
        # delete old entries
        for constraint in self.constraints_tree.get_children():
            self.constraints_tree.delete(constraint)

        # add current constraints
        for constraint in self.cfm.constraints:
            constraint_id = self.constraints_tree.insert("", "end", values=(constraint.first_feature.name,
                                                                            str(constraint.first_cardinality),
                                                                            "requires" if constraint.require else "excludes",
                                                                            constraint.second_feature.name,
                                                                            str(constraint.second_cardinality), "🖉",
                                                                            "🗑️"))

    def on_constraints_click(self, event):
        region = self.constraints_tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.constraints_tree.identify_column(event.x)
            row = self.constraints_tree.identify_row(event.y)

            if column == "#6":  # Edit column (where edit icon is displayed)
                print(f"Edit icon clicked for row {row}")
                # TODO

            elif column == "#7":  # Delete column (where delete icon is displayed)
                print(f"Delete icon clicked for row {row}")
                # TODO

    def toggle_children(self, event, feature):
        self.expanded_features[id(feature)] = not self.expanded_features.get(id(feature), True)
        self._draw_model()

    def on_right_click_node(self, event, feature):
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="Add Child", command=lambda: self.add_feature(feature))
        menu.add_command(label="Edit Feature", command=lambda: self.edit_feature(feature))
        menu.add_command(label="Delete Feature", command=lambda: self.delete_feature(feature))
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
            feature.parent.children.remove(feature)
            self._draw_model()

        # inner node
        else:
            self.show_delete_dialog(feature)

    # This is only used for inner nodes, so it is safe to assume that the feature has children and a parent.
    def show_delete_dialog(self, feature: Feature):
        def submit(delete_subtree: bool):
            parent = feature.parent
            former_number_of_children = len(parent.children)
            if not delete_subtree:
                # Move its children to the parent at the index of the feature
                index = parent.children.index(feature)
                for child in reversed(feature.children):
                    parent.children.insert(index, child)
                    child.parent = parent
            parent.children.remove(feature)
            group_created = False
            if len(parent.children) == 0:
                parent.group_type_cardinality, parent.group_instance_cardinality = Cardinality(
                    []), Cardinality([])
            if len(parent.children) == 1:
                parent.group_type_cardinality, parent.group_instance_cardinality = derive_parent_group_cards_for_one_child(
                    parent.children[0].instance_cardinality)
            # A new group was created
            if len(parent.children) == 2 and former_number_of_children < 2:
                parent.group_type_cardinality, parent.group_instance_cardinality = derive_parent_group_cards_for_multiple_children(
                    [child.instance_cardinality for child in parent.children])
                group_created = True

            self._draw_model()
            dialog.destroy()
            if group_created:
                messagebox.showinfo("Group Created",
                                    "A new group was created. You can edit its cardinalities now.")
                self.show_feature_dialog(feature=parent)

        dialog = tk.Toplevel()
        dialog.title("Delete Method")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()

        label = tk.Label(dialog,
                         text=(
                             f"Choose the delete method for feature {feature.name}. Delete subtree will also delete all descendents, transfer will attach them to their grand-parent."
                         ),
                         wraplength=280,
                         justify="left",
                         )
        label.pack(pady=10)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Delete subtree", command=lambda: submit(True)).pack(side="left", padx=5)
        tk.Button(button_frame, text="Transfer", command=lambda: submit(False)).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)

        dialog.wait_window(dialog)

    # Used for adding and editing features. If feature is None, a new feature is added, otherwise the feature is edited.
    def show_feature_dialog(self, parent: Feature = None, feature: Feature = None):
        def on_submit():
            feature_name = name_var.get().strip()
            if not feature_name:
                messagebox.showerror("Input Error", "Feature name cannot be empty.")
                return
            if (feature_name in [f.name for f in self.cfm.features]) and (
                    not is_edit or (feature_name != feature.name)):
                messagebox.showerror("Input Error", "Feature name must be unique.")
                return

            raw_feature_card = feature_card_var.get().strip()
            feature_card = Cardinality([Interval(0, None)])
            if raw_feature_card:
                try:
                    feature_card = edit_str_to_cardinality(raw_feature_card)
                except ValueError:
                    messagebox.showerror("Input Error",
                                         "Invalid feature cardinality format. Use 'min,max' or 'min,*' for intervals.")
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
                        messagebox.showerror("Input Error",
                                             "Invalid group type cardinality format. Use 'min,max' or 'min,*' for intervals.")
                        return
                    try:
                        group_instance_card = edit_str_to_cardinality(raw_group_instance_card)
                    except ValueError:
                        messagebox.showerror("Input Error",
                                             "Invalid group instance cardinality format. Use 'min,max' or 'min,*' for intervals.")
                        return
                    feature.group_type_cardinality = group_type_card
                    feature.group_instance_cardinality = group_instance_card
                if is_only_child:
                    feature.parent.group_type_cardinality, feature.parent.group_instance_cardinality = derive_parent_group_cards_for_one_child(
                        feature.instance_cardinality)

            else:
                new_feature = Feature(
                    name=feature_name,
                    instance_cardinality=feature_card,
                    group_type_cardinality=Cardinality([]),
                    group_instance_cardinality=Cardinality([]),
                    parent=parent,
                    children=[]
                )
                self.expanded_features[id(new_feature)] = True  # Initialize new feature as expanded
                parent.children.append(new_feature)
                if len(parent.children) == 1:
                    parent.group_type_cardinality, parent.group_instance_cardinality = derive_parent_group_cards_for_one_child(
                        feature_card)
                if len(parent.children) == 2:
                    group_created = True
                    parent.group_type_cardinality, parent.group_instance_cardinality = derive_parent_group_cards_for_multiple_children(
                        [child.instance_cardinality for child in parent.children])

            self._draw_model()
            dialog.destroy()
            if group_created:
                messagebox.showinfo("Group Created",
                                    "A new group was created. You can edit its cardinalities now.")
                self.show_feature_dialog(feature=parent)

        dialog = Toplevel(self.root)
        dialog.withdraw()
        dialog.title("Edit Feature" if feature else "Add Feature")

        is_edit = feature is not None
        is_group = is_edit and len(feature.children) > 1
        is_only_child = is_edit and feature.parent and len(feature.parent.children) == 1

        current_name = feature.name if is_edit else ""
        current_feature_card = cardinality_to_edit_str(feature.instance_cardinality) if is_edit else ""

        Label(dialog, text="Feature Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        name_var = StringVar(value=current_name)
        Entry(dialog, textvariable=name_var).grid(row=0, column=1, padx=5, pady=5)

        Label(dialog, text="Feature cardinality (e.g., '1,2; 5,*'):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        feature_card_var = StringVar(value=current_feature_card)
        Entry(dialog, textvariable=feature_card_var).grid(row=1, column=1, padx=5, pady=5)

        if is_group:
            current_group_type_card = cardinality_to_edit_str(feature.group_type_cardinality)
            current_group_instance_card = cardinality_to_edit_str(feature.group_instance_cardinality)

            Label(dialog, text="Group type cardinality:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
            group_type_card_var = StringVar(value=current_group_type_card)
            Entry(dialog, textvariable=group_type_card_var).grid(row=2, column=1, padx=5, pady=5)

            Label(dialog, text="Group instance cardinality:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
            group_instance_card_var = StringVar(value=current_group_instance_card)
            Entry(dialog, textvariable=group_instance_card_var).grid(row=3, column=1, padx=5, pady=5)

        Button(dialog, text="Save changes" if is_edit else "Add", command=on_submit).grid(row=4, column=0, columnspan=2,
                                                                                          pady=10)

        # Center the dialog window
        self.root.update_idletasks()
        main_window_x = self.root.winfo_x()
        main_window_y = self.root.winfo_y()
        main_window_width = self.root.winfo_width()
        main_window_height = self.root.winfo_height()

        dialog_x = main_window_x + (main_window_width // 2) - (dialog.winfo_reqwidth() // 2)
        dialog_y = main_window_y + (main_window_height // 2) - (dialog.winfo_reqheight() // 2)

        dialog.geometry(f"+{dialog_x}+{dialog_y}")

        dialog.deiconify()
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.wait_window()
