from typing import List, Tuple
from math import ceil
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

    def __init__(self, cfm: CFM):
        self.cfm = cfm
        """The feature model to calculate the layout for."""

        self.pos = {id(feature): Point(0, 0) for feature in cfm.features}
        """The final positions of the features in the feature model."""

        self.shift = {id(feature): 0 for feature in cfm.features}
        """The x shifts of the features relative to their parent."""

    def compute_positions(self) -> dict[int, Point]:
        """Computes the coordinates of all features with the Reingold-Tilford algorithm. The dictionary can be accessed
        with the feature id."""
        self._compute_y(self.cfm.root, 0)
        self._compute_shift(self.cfm.root)
        self._compute_x(self.cfm.root)
        # get the lowest x coordinate and add the absolute value to all x coordinates to make them positive
        # min_x = min([pos.x for pos in self.pos.values()])
        # for feature in self.pos:
        #     self.pos[feature].x = self.pos[feature].x - min_x
        return self.pos

    def _compute_y(self, feature: Feature, depth: int):
        """The leveled y coordinate is calculated by a simple breadth-first traversal."""
        # TODO: Check what is a good distance between levels
        self.pos[id(feature)].y = depth * 50
        for child in feature.children:
            self._compute_y(child, depth + 1)

    def _compute_shift(self, feature: Feature) -> Tuple[List[int], List[int]]:
        """The shifts are calculated recursively from bottom to top. For each subtree, a contour is calculated that
        describes the left and right boundary of the subtree. These subtrees are then placed as close to each other as
        possible without overlapping. The parent is placed in the middle of the children and the shifts of the children
        are calculated relative to the parent."""
        children = feature.children
        if not children or len(children) == 0:
            return [-2 * len(feature.name)], [2 * len(feature.name)]
        else:
            contours = {}
            for child in children:
                contours[id(child)] = self._compute_shift(child)
            # d[i] is the distance between the (i-1)-th and the i-th child
            d = [0]
            for i in range(1, len(children)):
                d.append(0)
                sum_left = 0
                sum_right = 0
                # Make sure the contours never overlap
                for j in range(0, min(len(contours[id(children[i - 1])][1]), len(contours[id(children[i])][0]))):
                    sum_left += contours[id(children[i])][0][j]
                    sum_right += contours[id(children[i - 1])][1][j]
                    d[i] = max(d[i], sum_right - sum_left)
                # add padding
                # TODO: Check what is a good padding
                d[i] += 20
            total_distance = sum(d)

            accumulated_distance = 0
            for i in range(len(children)):
                accumulated_distance += d[i]
                self.shift[id(children[i])] = accumulated_distance - ceil(total_distance / 2)

            contour_left = [-2 * len(feature.name), self.shift[id(children[0])] + 2 * len(feature.name)]
            old_contour = contours[id(children[0])][0]
            contour_left.extend(old_contour[1:])
            curr_height = len(contour_left)
            for i in range(1, len(children)):
                if len(contours[id(children[i])][0]) >= curr_height:
                    old_contour = contours[id(children[i])][0]
                    contour_left.append(
                        sum(old_contour[0:curr_height]) + self.shift[id(children[i])] - self.shift[
                            id(children[i - 1])] - sum(
                            contours[id(children[i - 1])][0]))
                    contour_left.extend(old_contour[curr_height:len(old_contour)])
                    curr_height = len(contour_left)

            contour_right = [2 * len(feature.name), self.shift[id(children[-1])] + 2 * len(feature.name)]
            old_contour = contours[id(children[-1])][1]
            contour_right.extend(old_contour[1:])
            curr_height = len(contour_right)
            for i in range(len(children) - 2, -1, -1):
                if len(contours[id(children[i])][1]) >= curr_height:
                    old_contour = contours[id(children[i])][1]
                    contour_right.append(
                        sum(old_contour[0:curr_height]) + self.shift[id(children[i])] - self.shift[
                            id(children[i - 1])] - sum(
                            contours[id(children[i - 1])][1]))
                    contour_right.extend(old_contour[curr_height:len(old_contour)])
                    curr_height = len(contour_right)

            return contour_left, contour_right

    def _compute_x(self, feature: Feature):
        parent = feature.parent
        if parent is None:
            self.pos[id(feature)].x = 400
        else:
            self.pos[id(feature)].x = self.pos[id(parent)].x + self.shift[id(feature)]
        for child in feature.children:
            self._compute_x(child)
