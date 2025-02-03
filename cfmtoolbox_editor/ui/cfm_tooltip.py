import tkinter as tk
from tkinter import ttk


class ToolTip:
    """Tooltip class to show short texts when hovering a widget or canvas item."""

    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None

    def show_tip(self, text, x=None, y=None):
        """
        Show the tooltip with a specified text.
        :param text: Text to display in the tooltip
        :param x: Optional X coordinate (for canvas items)
        :param y: Optional Y coordinate (for canvas items)
        """
        self.hide_tip()
        if not text:
            return

        if x is None or y is None:  # Standard widget
            x, y, _, cy = self.widget.bbox("insert")
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 20
        else:
            if isinstance(self.widget, tk.Canvas):  # Canvas item: Adjust for scrolling
                x_offset = self.widget.winfo_rootx() - self.widget.canvasx(0)
                y_offset = self.widget.winfo_rooty() - self.widget.canvasy(0)
                x += x_offset + 10
                y += y_offset + 10
            else:
                x += self.widget.winfo_rootx() + 10
                y += self.widget.winfo_rooty() + 10

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.geometry(f"+{int(x)}+{int(y)}")
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
