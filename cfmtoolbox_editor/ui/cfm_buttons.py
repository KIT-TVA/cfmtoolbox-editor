import tkinter as tk
from tkinter import ttk


class CFMButtons:
    def __init__(self, parent, editor):
        self.parent = parent
        self.editor = editor
        self._create_buttons()

    def _create_buttons(self):
        self.button_frame = ttk.Frame(self.parent)
        self.button_frame.pack(side=tk.BOTTOM, pady=5)

        self.save_button = ttk.Button(
            self.button_frame, text="Save", command=self.editor._save_model
        )
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.reset_button = ttk.Button(
            self.button_frame, text="Reset", command=self.editor._reset_model
        )
        self.reset_button.pack(side=tk.LEFT, padx=5)

    def get_frame(self):
        return self.button_frame
