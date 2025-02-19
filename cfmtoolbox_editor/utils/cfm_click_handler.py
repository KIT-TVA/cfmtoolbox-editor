"""
This module defines the CFMClickHandler class, which is responsible for handling click events
in a cross-platform manner for the Tkinter library.

Classes:
    CFMClickHandler: A class to handle left and right click events for different operating systems.
"""

import sys


class CFMClickHandler:
    def __init__(self):
        """
        Initialize the CFMClickHandler and determine the operating system.
        """
        self.is_mac = sys.platform == "darwin"

    def left_click(self) -> str:
        """
        Returns the correct left-click event for the operating system.

        Returns:
            str: The left-click event string.
        """
        return "<Button-1>"

    def right_click(self) -> str:
        """
        Returns the correct right-click event for the operating system.

        Returns:
            str: The right-click event string.
        """
        return "<Button-2>" if self.is_mac else "<Button-3>"
