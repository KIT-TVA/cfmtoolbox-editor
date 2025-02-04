import sys


class CFMClickHandler:
    def __init__(self):
        self.is_mac = sys.platform == "darwin"

    def left_click(self) -> str:
        """Returns the correct left-click event for the operating system"""
        return "<Button-1>"

    def right_click(self) -> str:
        """Returns the correct right-click event for the operating system"""
        return "<Button-2>" if self.is_mac else "<Button-3>"
