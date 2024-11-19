import tkinter as tk
from tkinter import filedialog, simpledialog, Menu, messagebox
from logic import FeatureModel

class CFMEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CFM Editor")
        self.model = FeatureModel()

        self._setup_ui()

    def _setup_ui(self):
        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(expand=True, fill='both')

        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="New", command=self.new_model)
        self.file_menu.add_command(label="Open", command=self.open_model)
        self.file_menu.add_command(label="Save", command=self.save_model)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)

        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Add Feature", command=self.add_feature)
        self.edit_menu.add_command(label="Add Relation", command=self.add_relation)

        self.save_button = tk.Button(self.root, text="Save", command=self.save_model)
        self.save_button.pack(side='bottom')

        self.canvas.bind("<Button-3>", self.on_right_click)

    def new_model(self):
        self.model = FeatureModel()
        self.canvas.delete("all")

    def open_model(self):
        file_path = filedialog.askopenfilename(defaultextension=".uvl",
                                               filetypes=[("UVL Files", "*.uvl"), ("All Files", "*.*")])
        if file_path:
            self.model.load_from_uvl(file_path)
            self._draw_model()

    def save_model(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".uvl",
                                                 filetypes=[("UVL Files", "*.uvl"), ("All Files", "*.*")])
        if file_path:
            self.model.save_to_uvl(file_path)

    def add_feature(self, event=None):
        feature_name = simpledialog.askstring("Feature Name", "Enter feature name:")
        if feature_name:
            cardinality = simpledialog.askstring("Cardinality", "Enter cardinality (min, max):")
            if cardinality:
                min_card, max_card = map(int, cardinality.split(","))
                self.model.add_feature(feature_name, (min_card, max_card))
                self._draw_model()

    def add_relation(self):
        parent = simpledialog.askstring("Parent Feature", "Enter parent feature name:")
        child = simpledialog.askstring("Child Feature", "Enter child feature name:")
        if parent and child:
            if parent in self.model.features and child in self.model.features:
                self.model.add_relation(parent, child)
                self._draw_model()
            else:
                messagebox.showerror("Error", "Both features must exist to create a relation.")

    def _draw_model(self):
        self.canvas.delete("all")
        y_offset = 50
        self.feature_positions = {}
        for feature, cardinality in self.model.features.items():
            x, y = 100, y_offset
            text = f"{feature} [{cardinality[0]}, {cardinality[1]}]"
            text_id = self.canvas.create_text(x, y, text=text, tags=feature)
            bbox = self.canvas.bbox(text_id)
            rect_id = self.canvas.create_rectangle(bbox, fill="lightgrey")
            # Move the text to be on top of the rectangle
            self.canvas.tag_raise(text_id, rect_id)
            # Store the position of the feature
            self.feature_positions[feature] = (x, y)
            y_offset += 60
        for parent, child in self.model.relations:
            parent_pos = self.feature_positions.get(parent)
            child_pos = self.feature_positions.get(child)
            if parent_pos and child_pos:
                x1, y1 = parent_pos
                x2, y2 = child_pos
                # Draw a line between the center of the rectangles
                line_id = self.canvas.create_line(x1, y1 + 10, x2, y2 - 10)

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
                menu.add_command(label="Add Relation", command=lambda: self.add_relation_to_feature(feature_name))
        menu.post(event.x_root, event.y_root)

    def edit_feature(self, feature_name):
        new_name = simpledialog.askstring("Edit Feature", f"Edit feature name ({feature_name}):")
        if new_name:
            cardinality = simpledialog.askstring("Cardinality", "Enter cardinality (min, max):")
            if cardinality:
                min_card, max_card = map(int, cardinality.split(","))
                # Update the feature name and cardinality
                if feature_name in self.model.features:
                    del self.model.features[feature_name]
                    self.model.features[new_name] = (min_card, max_card)
                    # Update relations to use the new feature name
                    for i in range(len(self.model.relations)):
                        parent, child = self.model.relations[i]
                        if parent == feature_name:
                            parent = new_name
                        if child == feature_name:
                            child = new_name
                        self.model.relations[i] = (parent, child)
                    # Redraw the model
                    self._draw_model()

    def delete_feature(self, feature_name):
        # Remove the feature and its relations
        if feature_name in self.model.features:
            del self.model.features[feature_name]
            self.model.relations = [(p, c) for p, c in self.model.relations if p != feature_name and c != feature_name]
            # Redraw the model
            self._draw_model()

    def add_relation_to_feature(self, parent_feature):
        child_feature = simpledialog.askstring("Child Feature", "Enter child feature name:")
        if child_feature:
            if parent_feature in self.model.features and child_feature in self.model.features:
                # Add the relation and redraw the model
                self.model.add_relation(parent_feature, child_feature)
                self._draw_model()
            else:
                messagebox.showerror("Error", "Both features must exist to create a relation.")

if __name__ == "__main__":
    root = tk.Tk()
    app = CFMEditorApp(root)
    root.mainloop()