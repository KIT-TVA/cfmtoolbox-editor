import tkinter as tk
from tkinter import ttk


class ToolTip:
    """Tooltip class to show short texts when hovering a widget or canvas item."""

    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None

    def show_tip(self, text, x_pos: int = 0, y_pos: int = 0):
        """
        Show the tooltip with a specified text.
        :param text: Text to display in the tooltip
        :param x_pos: x coordinate relative to the widget
        :param y_pos: y coordinate relative to the widget
        """
        margin = 10

        self.hide_tip()
        if not text:
            return

        if isinstance(self.widget, tk.Canvas):  # Canvas item: Adjust for scrolling
            x_scroll = self.widget.winfo_rootx() - self.widget.canvasx(0)
            y_scroll = self.widget.winfo_rooty() - self.widget.canvasy(0)
            x_pos += x_scroll + margin
            y_pos += y_scroll + margin
        else:
            x, y, _, cy = self.widget.bbox("insert")
            x_pos += x + self.widget.winfo_rootx() + margin
            y_pos += y + self.widget.winfo_rooty() + margin

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.geometry(f"+{int(x_pos)}+{int(y_pos)}")
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
