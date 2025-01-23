import tkinter as tk
from tkinter import ttk


class ToolTip:
    """Tooltip class to show short texts when hovering a widget."""

    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None

    def show_tip(self, text):
        """
        Show the tooltip with a specified text.
        :param text: Text to display in the tooltip
        """
        self.hide_tip()
        if not text:
            return
        x, y, _, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.geometry(f"+{x}+{y}")
        label = ttk.Label(
            tw,
            text=text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("tahoma", 8, "normal"),
        )
        label.pack(ipadx=1)

    def hide_tip(self):
        """
        Hide the tooltip.
        """
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
