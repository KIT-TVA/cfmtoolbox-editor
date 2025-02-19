from typing import List, Tuple, Dict
from math import ceil, floor
from dataclasses import dataclass

from cfmtoolbox import CFM, Feature


@dataclass
class Point:
    x: int
    y: int


class GraphLayoutCalculator:
    """
    This class uses an adaption of the Reingold-Tilford algorithm to calculate the positions of the features in a
    feature model. It guarantees a planar drawing which is leveled and the parent is centered above its children.
    An adaption had to be made to account for the different lengths of feature names.
    """

    def __init__(
        self, cfm: CFM, expanded_features: dict[int, bool], max_node_width: int
    ):
        self.cfm = cfm
        """The feature model to calculate the layout for."""

        self.expanded_features = expanded_features
        """Only calculate positions for expanded features."""

        self.max_node_width: int = max_node_width
        """The maximum width of a node in the graph. If the text is longer, it will be cut off."""

        self.pos = {id(feature): Point(0, 0) for feature in cfm.features}
        """The final positions of the features in the feature model."""

        self.shift = {id(feature): 0 for feature in cfm.features}
        """The x shifts of the features relative to their parent."""

        self.scale_text = 3
        """The scaling factor from text length to pixel length."""

    def compute_positions(self) -> dict[int, Point]:
        """Computes the coordinates of all features with the Reingold-Tilford algorithm. The dictionary can be accessed
        with the feature id."""
        self._compute_y(self.cfm.root, 0)
        self._compute_shift(self.cfm.root)
        self._compute_x(self.cfm.root)
        return self.pos

    def _compute_y(self, feature: Feature, depth: int):
        """The leveled y coordinate is calculated by a simple breadth-first traversal."""
        self.pos[id(feature)].y = depth * 100 + 50
        if self.expanded_features[id(feature)]:
            for child in feature.children:
                self._compute_y(child, depth + 1)

    def _compute_shift(self, feature: Feature) -> Tuple[List[int], List[int]]:
        """
        The shifts are calculated recursively from bottom to top. For each subtree, a contour is calculated that
        describes the left and right boundary of the subtree. These subtrees are then placed as close to each other as
        possible without overlapping. The parent is placed in the middle of the children and the shifts of the children
        are calculated relative to the parent. The method returns the contour of the subtree and the shift is saved in
        the according field.
        :param feature: The current feature to calculate the shift for.
        :return: The left and right contour of the subtree rooted at the feature.
        """
        left_contour, right_contour = self._initialize_contours(feature)

        children = feature.children
        # Base case
        if (
            not self.expanded_features[id(feature)]
            or not children
            or len(children) == 0
        ):
            return left_contour, right_contour

        else:
            children_contours = {
                id(child): self._compute_shift(child) for child in feature.children
            }

            # d[i] is the distance between the (i-1)-th and the i-th child
            d, children_left_contour, children_right_contour = (
                self._calculate_distances(children, children_contours)
            )

            total_distance = sum(d)

            self._apply_shifts(children, d, total_distance)

            left_contour.append(
                self.shift[id(children[0])]
                + children_contours[id(children[0])][0][0]
                + min(
                    ceil(self.scale_text * len(feature.name)),
                    ceil(self.max_node_width / 2),
                )
            )
            left_contour.extend(children_left_contour[1:])

            right_contour.append(
                self.shift[id(children[-1])]
                + children_contours[id(children[-1])][1][0]
                - min(
                    ceil(self.scale_text * len(feature.name)),
                    ceil(self.max_node_width / 2),
                )
            )
            right_contour.extend(children_right_contour[1:])

            return left_contour, right_contour

    def _initialize_contours(self, feature: Feature) -> Tuple[List[int], List[int]]:
        """Initializes the left and right contours based on the feature's name length."""
        left = [
            max(
                floor(-self.scale_text * len(feature.name)),
                floor(-self.max_node_width / 2),
            )
        ]
        right = [
            min(
                ceil(self.scale_text * len(feature.name)), ceil(self.max_node_width / 2)
            )
        ]
        return left, right

    def _compute_x(self, feature: Feature):
        """
        The x coordinate is calculated by adding the shift of the feature to the position of the parent.
        :param feature: The feature to calculate the x coordinate for.
        """
        parent = feature.parent
        if parent is None:
            self.pos[id(feature)].x = 400
        else:
            self.pos[id(feature)].x = self.pos[id(parent)].x + self.shift[id(feature)]

        if self.expanded_features[id(feature)]:
            for child in feature.children:
                self._compute_x(child)

    def _calculate_distances(
            self,
            children: List[Feature],
            children_contours: Dict[int, Tuple[List[int], List[int]]],
    ) -> Tuple[List[int], List[int], List[int]]:
        """
        Calculate the distances between the children and update the contours of the subtree.
        :param children: Siblings in the subtree.
        :param children_contours: Recursively computed contours of the children.
        :return: The distances between the children and the contours of the subtree.
        """
        # d[i] is the distance between the (i-1)-th and the i-th child
        d = [0] * len(children)
        current_right_contour = children_contours[id(children[0])][1]
        current_left_contour = children_contours[id(children[0])][0]
        # Recursively merge the subtrees from left to right and update the right contour to avoid overlapping
        # non-neighbouring subtrees.
        for i in range(1, len(children)):
            sum_left = 0
            sum_right = 0
            next_left_contour = children_contours[id(children[i])][0]

            # Make sure the contours never overlap
            for j in range(min(len(current_right_contour), len(next_left_contour))):
                sum_left += next_left_contour[j]
                sum_right += current_right_contour[j]
                d[i] = max(d[i], sum_right - sum_left)
            # add padding
            d[i] += 50

            # update contours of subtrees merged so far
            new_right_contour = children_contours[id(children[i])][1]
            current_height_right = len(new_right_contour)
            if len(current_right_contour) > current_height_right:
                # old contour still visible
                new_right_contour.append(
                    -sum(new_right_contour)
                    - d[i]
                    + sum(current_right_contour[0: current_height_right + 1])
                )
                new_right_contour.extend(
                    current_right_contour[
                    current_height_right + 1: len(current_right_contour)
                    ]
                )
            current_right_contour = new_right_contour

            current_height_left = len(current_left_contour)
            if (len(next_left_contour)) > current_height_left:
                # new contour visible
                current_left_contour.append(
                    -sum(current_left_contour)
                    + d[i]
                    + sum(next_left_contour[0: current_height_left + 1])
                )
                current_left_contour.extend(
                    next_left_contour[current_height_left + 1: len(next_left_contour)]
                )
        return d, current_left_contour, current_right_contour

    def _apply_shifts(self, children: List[Feature], d: List[int], total_distance: int):
        accumulated_distance = 0
        for i in range(len(children)):
            accumulated_distance += d[i]
            self.shift[id(children[i])] = accumulated_distance - ceil(
                total_distance / 2
            )
