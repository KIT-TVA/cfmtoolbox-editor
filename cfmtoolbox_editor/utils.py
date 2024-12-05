from cfmtoolbox import Cardinality, Interval


def cardinality_to_display_str(cardinality: Cardinality, left_bracket: str, right_bracket: str) -> str:
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
        min_card, max_card = interval.split(",")
        min_card = int(min_card.strip())
        max_card = None if max_card.strip() == "*" else int(max_card.strip())
        intervals.append(Interval(min_card, max_card))
    return Cardinality(intervals)


def derive_parent_group_cardinalities(child_instance_card: Cardinality) -> (Cardinality, Cardinality):
    """
    Derives the parent group cardinalities from the only child's instance cardinality. Group type cardinality is 0 if
    the child can have 0 instances, 1 otherwise. Group instance cardinality is the same as the child's instance
    cardinality.
    :param child_instance_card: The feature instance cardinality of a child with no siblings
    :return: (Group type cardinality, Group instance cardinality) of the parent group
    """
    lower_group_type = 0 if any(interval.lower == 0 for interval in child_instance_card.intervals) else 1
    return Cardinality([Interval(lower_group_type, 1)]), Cardinality(child_instance_card.intervals)
