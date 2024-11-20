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

        self._setup_ui()

    def start(self, cfm):
        self.cfm = cfm
        # Make a deep copy of the CFM to be able to undo changes
        self.original_cfm = deepcopy(cfm)
        self._draw_model()
        self.root.mainloop()

    def _setup_ui(self):
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="white")
        self.canvas.pack(expand=True, fill='both')

        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)

        # TODO: Add Reset Button
        # TODO: On save, ask for confirmation before closing
        self.model_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.save_button = tk.Button(self.root, text="Save", command=self.root.quit)
        self.save_button.pack(side='bottom')

        self.canvas.bind("<Button-3>", self.on_right_click)

    def add_feature(self, event=None):
        feature_name = simpledialog.askstring("Feature Name", "Enter feature name:")
        if feature_name:
            cardinality = simpledialog.askstring("Cardinality", "Enter cardinality (min, max):")
            if cardinality:
                min_card, max_card = map(int, cardinality.split(","))
                new_feature = Feature(name=feature_name,
                                      instance_cardinality=Cardinality([Interval(min_card, max_card)]),
                                      group_type_cardinality=Cardinality([]),
                                      group_instance_cardinality=Cardinality([]), parent=self.cfm.root, children=[])
                self.cfm.root.children.append(new_feature)
                self._draw_model()

    # TODO: Calculate more suitable feature positions
    def _draw_model(self):
        self.canvas.delete("all")
        self.draw_feature(self.cfm.root, 400, 50)

    def draw_feature(self, feature: Feature, x: int, y: int, x_offset:int = 200):
        # TODO: Handle multiple intervals
        cardinality_interval = feature.instance_cardinality.intervals[0]
        text = f"{feature} [{cardinality_interval.lower}, {cardinality_interval.upper}]"
        node_id = self.canvas.create_text(x, y, text=text, tags=feature.name)
        bbox = self.canvas.bbox(node_id)
        rect_id = self.canvas.create_rectangle(bbox, fill="lightgrey")
        # Move the text to be on top of the rectangle
        self.canvas.tag_raise(node_id, rect_id)

        # Recursively draw children
        if feature.children:
            new_y = y + 50
            for i, child in enumerate(feature.children):
                new_x = x - x_offset + (i * ((2 * x_offset) // (len(feature.children) - 1)))
                self.canvas.create_line(x, y + 10, new_x, new_y - 10, tags="edge", arrow=tk.LAST)
                self.draw_feature(child, new_x, new_y, x_offset // 2)

    # TODO: Can we make the nodes actually clickable? (bind this to the nodes)
    def on_right_click(self, event):
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="Add Feature", command=lambda: self.add_feature(event))
        item = self.canvas.find_closest(event.x, event.y)
        if item:
            tags = self.canvas.gettags(item)
            if tags:
                feature_name = tags[0]
                menu.add_command(label="Edit Feature", command=lambda: self.edit_feature(feature_name))
                menu.add_command(label="Delete Feature", command=lambda: self.delete_feature(feature_name))
        menu.post(event.x_root, event.y_root)

    def edit_feature(self, feature_name):
        new_name = simpledialog.askstring("Edit Feature", f"Edit feature name ({feature_name}):")
        if new_name:
            cardinality = simpledialog.askstring("Cardinality", "Enter cardinality (min, max):")
            if cardinality:
                min_card, max_card = map(int, cardinality.split(","))
                # Update the feature name and cardinality
                feature = next((feature for feature in self.cfm.features if feature.name == feature_name), None)
                if feature:
                    feature.name = new_name
                    feature.instance_cardinality = Cardinality([Interval(min_card, max_card)])
                    self._draw_model()

    def delete_feature(self, feature_name):
        # Remove the feature and its relations
        feature = next((feature for feature in self.cfm.features if feature.name == feature_name), None)
        if feature:
            self.cfm.features.remove(feature)
            if feature.parent:
                feature.parent.children.remove(feature)
            # Redraw the model
            self._draw_model()
