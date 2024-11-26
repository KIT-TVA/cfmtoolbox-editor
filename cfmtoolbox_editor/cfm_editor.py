import tkinter as tk
from copy import deepcopy
from tkinter import ttk
from tkinter import simpledialog, Menu

from cfmtoolbox import Cardinality, Interval, Feature


class CFMEditorApp:
    def __init__(self):
        self.cfm = None
        self.original_cfm = None
        self.root = tk.Tk()
        self.root.title("CFM Editor")
        self.feature_states = {}  # Dictionary to track expanded/collapsed state of features

        self._setup_ui()

    def start(self, cfm):
        self.cfm = cfm
        # Make a deep copy of the CFM to be able to undo changes
        self.original_cfm = deepcopy(cfm)
        self._initialize_feature_states(self.cfm.root)
        self._draw_model()
        self.root.mainloop()

    def _initialize_feature_states(self, feature):
        self.feature_states[id(feature)] = True  # Initialize all features as expanded
        for child in feature.children:
            self._initialize_feature_states(child)

    def _setup_ui(self):
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="white")
        self.canvas.pack(expand=True, fill='both')

        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self._exit_application)

        self.model_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.menu_bar.add_cascade(label="Model", menu=self.model_menu)

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
        self.draw_feature(self.cfm.root, 400, 50)

    def draw_feature(self, feature: Feature, x: int, y: int, x_offset: int = 200):
        # TODO: Handle multiple intervals
        # TODO: First check if intervals exist
        feature_instance_cardinality = feature.instance_cardinality.intervals[
            0] if feature.instance_cardinality.intervals else Interval(0, 0)
        group_type_cardinality = feature.group_type_cardinality.intervals[
            0] if feature.group_type_cardinality.intervals else Interval(0, 0)
        group_instance_cardinality = feature.group_instance_cardinality.intervals[
            0] if feature.group_instance_cardinality.intervals else Interval(0, 0)

        node_id = self.canvas.create_text(x, y, text=feature.name, tags=feature.name)
        # TODO: Add padding to the rectangle
        bbox = self.canvas.bbox(node_id)
        rect_id = self.canvas.create_rectangle(bbox, fill="lightgrey")
        self.canvas.tag_raise(node_id, rect_id)

        # bbox[1] is the y-coordinate of the top side of the box
        feature_instance_y = bbox[1] - 10
        feature_instance_x = x - 20
        # TODO: The brackets don't look nice
        # TODO: Position on right of arrow for children on the right and central for root
        feature_instance_text = f"<{feature_instance_cardinality.lower}, {feature_instance_cardinality.upper}>"
        feature_instance_id = self.canvas.create_text(feature_instance_x, feature_instance_y,
                                                      text=feature_instance_text,
                                                      tags=f"{feature.name}_feature_instance")

        # TODO: Add half circle for group
        # bbox[3] is the y-coordinate of the bottom of the text box
        group_type_y = bbox[3] + 10
        group_type_text = f"[{group_type_cardinality.lower}, {group_type_cardinality.upper}]"
        group_type_id = self.canvas.create_text(x, group_type_y, text=group_type_text,
                                                tags=f"{feature.name}_group_type")

        group_instance_text = f"<{group_instance_cardinality.lower}, {group_instance_cardinality.upper}>"

        # Add collapse/expand button
        if feature.children:
            expanded = self.feature_states.get(id(feature), True)
            button_text = "-" if expanded else "+"
            button_id = self.canvas.create_text(bbox[2] + 10, bbox[3], text=button_text, tags="button")
            # Button-1 is left mouse button
            self.canvas.tag_bind(button_id, "<Button-1>", lambda event, f=feature: self.toggle_children(event, f))

        # Click event handling (Button-1 is left mouse button, Button-3 is right mouse button)
        # self.canvas.tag_bind(node_id, "<Button-1>", lambda event, f=feature: self.on_left_click_node(event, f))
        self.canvas.tag_bind(node_id, "<Button-3>", lambda event, f=feature: self.on_right_click_node(event, f))

        # Recursively draw children if expanded
        if feature.children and self.feature_states.get(id(feature), True):
            new_y = y + 100
            for i, child in enumerate(feature.children):
                new_x = x if len(feature.children) == 1 else x - x_offset + (
                        i * ((2 * x_offset) // (len(feature.children) - 1)))
                self.canvas.create_line(x, y + 10, new_x, new_y - 10, tags="edge", arrow=tk.LAST)
                # TODO: Should group instance cardinality be displayed when there are no children / they aren't expanded?
                if i == len(feature.children) - 1:
                    # Calculate text position for group instance cardinality with linear interpolation
                    slope = (new_x - x) / (new_y - 10 - (y + 10))
                    group_instance_y = bbox[3] + 10
                    group_instance_x = x + slope * (group_instance_y - (y + 10)) + 5
                    # anchor w means west, so the left side of the text is placed at the specified position
                    self.canvas.create_text(group_instance_x, group_instance_y, text=group_instance_text,
                                            tags=f"{feature.name}_group_instance", anchor="w")
                self.draw_feature(child, new_x, new_y, x_offset // 2)

    def toggle_children(self, event, feature):
        self.feature_states[id(feature)] = not self.feature_states.get(id(feature), True)
        self._draw_model()

    # TODO: Can we make the nodes actually clickable? (bind this to the nodes)
    def on_right_click_node(self, event, feature):
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="Add Child", command=lambda: self.add_feature(feature))
        menu.add_command(label="Edit Feature", command=lambda: self.edit_feature(feature))
        menu.add_command(label="Delete Feature", command=lambda: self.delete_feature(feature))
        menu.post(event.x_root, event.y_root)

    def add_feature(self, parent):
        feature_name = simpledialog.askstring("Feature Name", "Enter feature name:")
        if feature_name:
            cardinality = simpledialog.askstring("Cardinality", "Enter cardinality (min, max):")
            if cardinality:
                min_card, max_card = map(int, cardinality.split(","))
                new_feature = Feature(name=feature_name,
                                      instance_cardinality=Cardinality([Interval(min_card, max_card)]),
                                      group_type_cardinality=Cardinality([]),
                                      group_instance_cardinality=Cardinality([]), parent=parent, children=[])
                self.feature_states[id(new_feature)] = True  # Initialize new feature as expanded
                parent.children.append(new_feature)
                self._draw_model()

    def edit_feature(self, feature):
        new_name = simpledialog.askstring("Edit Feature", f"Edit feature name ({feature.name}):")
        if new_name:
            cardinality = simpledialog.askstring("Cardinality", "Enter cardinality (min, max):")
            if cardinality:
                min_card, max_card = map(int, cardinality.split(","))
                # Update the feature name and cardinality
                feature.name = new_name
                feature.instance_cardinality = Cardinality([Interval(min_card, max_card)])
                self._draw_model()

    def delete_feature(self, feature):
        self.cfm.features.remove(feature)
        if feature.parent:
            feature.parent.children.remove(feature)
        self._draw_model()
