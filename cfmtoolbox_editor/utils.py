from cfmtoolbox import Cardinality


def cardinality_to_str(cardinality: Cardinality, left_bracket: str, right_bracket: str) -> str:
    intervals = cardinality.intervals
    if not intervals:
        return f"{left_bracket}{right_bracket}"
    string_rep = ""
    for interval in intervals:
        string_rep += f"{left_bracket}{interval.lower}, {"*" if interval.upper is None else interval.upper}{right_bracket}, "
    # Remove the last comma and space
    string_rep = string_rep[:-2]
    return string_rep
