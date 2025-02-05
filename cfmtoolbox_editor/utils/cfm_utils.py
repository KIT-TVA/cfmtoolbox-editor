import tkinter as tk
from typing import Tuple, List

from cfmtoolbox import Cardinality, Interval


def cardinality_to_display_str(
    cardinality: Cardinality, left_bracket: str, right_bracket: str
) -> str:
    """
    Converts a cardinality to a string representation that is displayed in the editor.
    :param cardinality: The cardinality to display
    :param left_bracket: The left symbol to use for the intervals
    :param right_bracket: The right symbol to use for the intervals
    :return: The string representation of the cardinality using the specified brackets
    """
    intervals = cardinality.intervals
    if not intervals:
        return f"{left_bracket}{right_bracket}"

    return ", ".join(
        f"{left_bracket}{interval.lower}, {'*' if interval.upper is None else interval.upper}{right_bracket}"
        for interval in intervals
    )


def cardinality_to_edit_str(cardinality: Cardinality) -> str:
    """
    Converts a cardinality to a string representation of the intervals that can be edited by the user.
    :param cardinality: The cardinality to convert
    :return: A string representation of the intervals separating bounds by comma and intervals by semicolon
    """
    return "; ".join(
        f"{interval.lower},{'*' if interval.upper is None else interval.upper}"
        for interval in cardinality.intervals
    )


def edit_str_to_cardinality(raw_cardinality: str) -> Cardinality:
    """
    Converts intervals entered by the user to a Cardinality object.
    :param raw_cardinality: The intervals to parse
    :return: The Cardinality object constructed from the parsed intervals
    :raises ValueError: If the intervals are not formatted correctly (Bounds have to be ints or * separated by a comma, intervals are separated by a semicolon)
    """
    intervals = []
    for interval in raw_cardinality.split(";"):
        min_str, max_str = interval.split(",")
        min_card = int(min_str.strip())
        max_card = None if max_str.strip() == "*" else int(max_str.strip())
        intervals.append(Interval(min_card, max_card))
    return Cardinality(intervals)


def derive_parent_group_cards_for_one_child(
    child_instance_card: Cardinality,
) -> Tuple[Cardinality, Cardinality]:
    """
    Derives the parent group cardinalities from the only child's instance cardinality. Group type cardinality is 0 if
    the child can have 0 instances, 1 otherwise. Group instance cardinality is the same as the child's instance
    cardinality.
    :param child_instance_card: The feature instance cardinality of a child with no siblings
    :return: (Group type cardinality, Group instance cardinality) of the parent group
    """
    lower_group_type = (
        0
        if any(interval.lower == 0 for interval in child_instance_card.intervals)
        else 1
    )
    return Cardinality([Interval(lower_group_type, 1)]), Cardinality(
        child_instance_card.intervals
    )


def derive_parent_group_cards_for_multiple_children(
    child_instance_cards: List[Cardinality],
) -> Tuple[Cardinality, Cardinality]:
    """
    Derives the parent group cardinalities from the instance cardinalities of multiple children. Group type cardinality
    is [mandatory children, all children]. Group instance cardinality is <sum of minimum lower bounds, sum of maximum
    upper bounds> of the children.
    :param child_instance_cards: The feature instance cardinalities of the children
    :return: (Group type cardinality, Group instance cardinality) of the parent group
    """
    lower_group_type = len(
        [
            card
            for card in child_instance_cards
            if not any(interval.lower == 0 for interval in card.intervals)
        ]
    )
    upper_group_type = len(child_instance_cards)
    lower_group_instance = sum(
        min(interval.lower for interval in card.intervals)
        for card in child_instance_cards
        if card.intervals
    )
    upper_group_instance = (
        None
        if any(
            interval.upper is None
            for card in child_instance_cards
            for interval in card.intervals
        )
        else sum(
            max(
                interval.upper
                for interval in card.intervals
                if interval.upper is not None
            )
            for card in child_instance_cards
            if card.intervals
        )
    )
    return (
        Cardinality([Interval(lower_group_type, upper_group_type)]),
        Cardinality([Interval(lower_group_instance, upper_group_instance)]),
    )


def center_window(
    parent_widget: tk.Widget, window_width: int, window_height: int
) -> Tuple[int, int]:
    """
    Calculates the position of the window to appear centered relative to the parent widget.
    :param parent_widget: The widget in which to center the window
    :param window_width: The width of the window in pixels
    :param window_height: The height of the window in pixels
    :return: The x and y coordinate of the top left corner of the window
    """
    parent_widget.update_idletasks()
    main_window_x = parent_widget.winfo_x()
    main_window_y = parent_widget.winfo_y()
    main_window_width = parent_widget.winfo_width()
    main_window_height = parent_widget.winfo_height()

    window_x = main_window_x + (main_window_width // 2) - (window_width // 2)
    window_y = main_window_y + (main_window_height // 2) - (window_height // 2)

    return window_x, window_y
