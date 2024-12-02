from math import atan2, degrees
import tkinter as tk
from copy import deepcopy
from tkinter import simpledialog, Menu, Toplevel, Label, Entry, Button, StringVar, messagebox
from tkinter.font import Font

from cfmtoolbox import Cardinality, Interval, Feature

from cfmtoolbox_editor.utils import cardinality_to_str


class CFMEditorApp:
    def __init__(self):
        self.cfm = None
        self.original_cfm = None
        self.root = tk.Tk()
        self.root.title("CFM Editor")
        self.expanded_features = {}  # Dictionary to track expanded/collapsed state of features

        self._setup_ui()

    def start(self, cfm):
        self.cfm = cfm
        # Make a deep copy of the CFM to be able to undo changes
        self.original_cfm = deepcopy(cfm)
        self._initialize_feature_states(self.cfm.root)
        self._draw_model()
        self.root.mainloop()

    def _initialize_feature_states(self, feature):
        self.expanded_features[id(feature)] = True  # Initialize all features as expanded
        for child in feature.children:
            self._initialize_feature_states(child)

    def _setup_ui(self):
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="white")
        self.canvas.pack(expand=True, fill='both')

        button_frame = tk.Frame(self.root)
        button_frame.pack(side='bottom', pady=5)

        self.save_button = tk.Button(button_frame, text="Save", command=self._save_model)
        self.save_button.pack(side='left', padx=5)

        self.reset_button = tk.Button(button_frame, text="Reset", command=self._reset_model)
        self.reset_button.pack(side='left', padx=5)

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
        self.canvas.delete("all")
        self.draw_feature(self.cfm.root, "middle", 400, 50)

    # TODO: Refactor this method as it became too long
    def draw_feature(self, feature: Feature, feature_instance_card_pos: str, x: int, y: int, x_offset: int = 200):
        node_id = self.canvas.create_text(x, y, text=feature.name, tags=feature.name)
        bbox = self.canvas.bbox(node_id)
        padding_x = 4
        padding_y = 2
        padded_bbox = (bbox[0] - padding_x, bbox[1] - padding_y, bbox[2] + padding_x, bbox[3] + padding_y)
        rect_id = self.canvas.create_rectangle(padded_bbox, fill="lightgrey")
        self.canvas.tag_raise(node_id, rect_id)

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
                                                      text=cardinality_to_str(feature.instance_cardinality, "<", ">"),
                                                      tags=f"{feature.name}_feature_instance", anchor=anchor)

        # bbox[3] is the y-coordinate of the bottom of the text box
        group_type_y = padded_bbox[3] + 10
        group_type_id = self.canvas.create_text(x, group_type_y,
                                                text=cardinality_to_str(feature.group_type_cardinality, "[", "]"),
                                                tags=f"{feature.name}_group_type")

        # Add collapse/expand button
        if feature.children:
            expanded = self.expanded_features.get(id(feature), True)
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
            # TODO: What if there are no or only one child(ren)
            arc_radius = 25
            x_center = x
            y_center = y + 10
            left_angle = 180
            right_angle = 360

            new_y = y + 100
            for i, child in enumerate(feature.children):
                new_x = x if len(feature.children) == 1 else x - x_offset + (
                        i * ((2 * x_offset) // (len(feature.children) - 1)))
                edge_id = self.canvas.create_line(x, y + 10, new_x, new_y - 10, tags="edge", arrow=tk.LAST)

                # Calculate angles for the group arc and adjust to canvas coordinate system
                if i == 0:
                    left_angle = (degrees(atan2((new_y - y_center), (new_x - x_center))) + 180) % 360
                if i == len(feature.children) - 1:
                    right_angle = (degrees(atan2((new_y - y_center), (new_x - x_center))) + 180) % 360

                    # TODO: Should group instance cardinality be displayed when there are no children / they aren't expanded?
                    # Calculate text position for group instance cardinality with linear interpolation
                    slope = (new_x - x) / (new_y - 10 - (y + 10))
                    group_instance_y = padded_bbox[3] + 10
                    group_instance_x = x + slope * (group_instance_y - (y + 10)) + 5
                    # anchor w means west, so the left side of the text is placed at the specified position
                    self.canvas.create_text(group_instance_x, group_instance_y,
                                            text=cardinality_to_str(feature.group_instance_cardinality, "<", ">"),
                                            tags=f"{feature.name}_group_instance", anchor=tk.W)
                child_feature_instance_card_pos = "right" if new_x >= x else "left"
                self.draw_feature(child, child_feature_instance_card_pos, new_x, new_y, round(x_offset / 3.5))

            arc_id = self.canvas.create_arc(x_center - arc_radius, y_center - arc_radius, x_center + arc_radius,
                                            y_center + arc_radius, fill="white", style=tk.PIESLICE, tags="arc",
                                            start=left_angle, extent=right_angle - left_angle)
            self.canvas.tag_raise(group_type_id, arc_id)

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
        self.cfm.features.remove(feature)
        if feature.parent:
            feature.parent.children.remove(feature)
        self._draw_model()

    # Used for adding and editing features. If feature is None, a new feature is added, otherwise the feature is edited.
    def show_feature_dialog(self, parent=None, feature=None):
        def on_submit():
            feature_name = name_var.get().strip()
            # TODO: Check if the feature name is unique
            if not feature_name:
                messagebox.showerror("Input Error", "Feature name cannot be empty.")
                return

            raw_cardinality = cardinality_var.get().strip()
            intervals = []
            if raw_cardinality:
                try:
                    for interval in raw_cardinality.split(";"):
                        min_card, max_card = interval.split(",")
                        min_card = int(min_card.strip())
                        max_card = None if max_card.strip() == "*" else int(max_card.strip())
                        intervals.append(Interval(min_card, max_card))
                except ValueError:
                    messagebox.showerror("Input Error",
                                         "Invalid cardinality format. Use 'min,max' or 'min,*' for intervals.")
                    return

            if feature:
                feature.name = feature_name
                feature.instance_cardinality = Cardinality(intervals)
            else:
                new_feature = Feature(
                    name=feature_name,
                    instance_cardinality=Cardinality(intervals),
                    group_type_cardinality=Cardinality([]),
                    group_instance_cardinality=Cardinality([]),
                    parent=parent,
                    children=[]
                )
                self.expanded_features[id(new_feature)] = True  # Initialize new feature as expanded
                parent.children.append(new_feature)

            self._draw_model()
            dialog.destroy()

        dialog = Toplevel(self.root)
        dialog.withdraw()
        dialog.title("Edit Feature" if feature else "Add Feature")

        current_name = feature.name if feature else ""
        current_cardinality = "; ".join(
            f"{interval.lower},{'*' if interval.upper is None else interval.upper}"
            for interval in (feature.instance_cardinality.intervals if feature else [])
        )

        Label(dialog, text="Feature Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        name_var = StringVar(value=current_name)
        Entry(dialog, textvariable=name_var).grid(row=0, column=1, padx=5, pady=5)

        Label(dialog, text="Cardinality (e.g., '1,2; 5,*'):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        cardinality_var = StringVar(value=current_cardinality)
        Entry(dialog, textvariable=cardinality_var).grid(row=1, column=1, padx=5, pady=5)

        Button(dialog, text="Submit", command=on_submit).grid(row=2, column=0, columnspan=2, pady=10)

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
