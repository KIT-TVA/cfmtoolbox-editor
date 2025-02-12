"""
This module defines the CFMCanvas class, which is responsible for rendering and interacting with a feature model
using the Tkinter library. The CFMCanvas class provides functionalities to draw features, manage their expanded/collapsed
states, and handle user interactions such as adding, editing, and deleting features, as well as adding constraints between them.

Classes:
    CFMCanvas: A class to create and manage a canvas for displaying and interacting with a feature model.
"""

import tkinter as tk
from math import degrees, atan2
from tkinter import ttk, messagebox
from tkinter.font import Font
from typing import Dict

from cfmtoolbox import Feature

from cfmtoolbox_editor.ui.cfm_tooltip import ToolTip
from cfmtoolbox_editor.utils.cfm_calc_graph_Layout import Point, GraphLayoutCalculator
from cfmtoolbox_editor.utils.cfm_utils import cardinality_to_display_str


class CFMCanvas:
    def __init__(
        self,
        main_frame,
        tk_root,
        editor,
        click_handler,
    ):
        self.main_frame = main_frame
        self.tk_root = tk_root
        self.editor = editor
        self.click_handler = click_handler

        self.expanded_features: Dict[
            int, bool
        ] = {}  # Dictionary to track expanded/collapsed state of features
        self.positions: Dict[int, Point] = {}
        self.currently_highlighted_feature: Feature | None = None

        self.info_label = None
        self.cancel_button_window = None

        self.CARDINALITY_FONT = ("Arial", 8)
        self.MAX_NODE_WIDTH = 120

        self._create_canvas()

    def initialize(self):
        """
        Initialize the canvas by setting the initial states of all features.
        """
        self.initialize_feature_states(self.editor.cfm.root)

    def initialize_feature_states(self, feature):
        """
        Recursively initialize the expanded/collapsed states of all features.

        Args:
            feature (Feature): The feature to initialize.
        """
        # Initialize all features as expanded
        self.expanded_features[id(feature)] = True
        for child in feature.children:
            self.initialize_feature_states(child)

    def _create_canvas(self):
        self._create_scrollbars()

        self.canvas = tk.Canvas(
            self.main_frame,
            bg="white",
            width=800,
            height=400,
            scrollregion=(0, 0, 1000, 1000),
        )
        self.canvas.config(
            yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set
        )
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

    def _create_scrollbars(self):
        self.v_scroll = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tk_root.update()
        self.h_scroll = ttk.Scrollbar(self.main_frame, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X, padx=self.v_scroll.winfo_width())

    def clear(self):
        """
        Clear all elements from the canvas.
        """
        self.canvas.delete("all")

    def configure_scroll_region(self, x_min, y_min, x_max, y_max):
        """
        Configure the scroll region of the canvas.

        Args:
            x_min (int): Minimum x-coordinate of the scroll region.
            y_min (int): Minimum y-coordinate of the scroll region.
            x_max (int): Maximum x-coordinate of the scroll region.
            y_max (int): Maximum y-coordinate of the scroll region.
        """
        self.canvas.config(scrollregion=(x_min, y_min, x_max, y_max))

    def draw_model(self):
        """
        Draw the entire feature model on the canvas.
        """
        self.positions = GraphLayoutCalculator(
            self.editor.cfm, self.expanded_features, self.MAX_NODE_WIDTH
        ).compute_positions()
        self.clear()
        self._draw_feature(self.editor.cfm.root, "middle")

        min_x = min(pos.x for pos in self.positions.values())
        max_x = max(pos.x for pos in self.positions.values())
        max_y = max(pos.y for pos in self.positions.values())

        padding_x = 100
        padding_y = 50
        self.configure_scroll_region(
            min(min_x - padding_x, 0), 0, max_x + padding_x, max_y + padding_y
        )

    def _draw_feature(self, feature: Feature, feature_instance_card_pos: str):
        x, y = self.positions[id(feature)].x, self.positions[id(feature)].y
        node_id, padded_bbox = self._draw_node(feature, x, y)

        if not feature == self.editor.cfm.root:
            self._draw_feat_instance_card(
                feature, feature_instance_card_pos, padded_bbox, x
            )

        if feature.children:
            self._draw_collapse_expand_button(feature, padded_bbox, y)

        self.canvas.tag_bind(
            node_id,
            self.click_handler.right_click(),
            lambda event, f=feature: self._on_right_click_node(event, f),
        )

        self.canvas.tag_bind(
            node_id,
            self.click_handler.left_click(),
            lambda event, f=feature: self._on_left_click_node(event, f),
        )

        # Recursively draw children if expanded
        if feature.children and self.expanded_features.get(id(feature), True):
            # arc for group
            arc_radius = 35
            x_center = x
            y_center = y + 10
            left_angle = 180.0
            right_angle = 360.0

            for i, child in enumerate(feature.children):
                new_x = self.positions[id(child)].x
                new_y = self.positions[id(child)].y
                self.canvas.create_line(
                    x, y + 10, new_x, new_y - 10, tags="edge", arrow=tk.LAST
                )

                # Calculate angles for the group arc and adjust to canvas coordinate system
                if i == 0:
                    left_angle = (
                        degrees(atan2((new_y - y_center), (new_x - x_center))) + 180
                    ) % 360
                if (i == len(feature.children) - 1) and (len(feature.children) > 1):
                    right_angle = (
                        degrees(atan2((new_y - y_center), (new_x - x_center))) + 180
                    ) % 360

                    self._draw_group_instance_card(
                        feature, new_x, new_y, padded_bbox, x, y
                    )

                child_feature_instance_card_pos = "right" if new_x >= x else "left"
                self._draw_feature(child, child_feature_instance_card_pos)

            if len(feature.children) > 1:
                self.canvas.create_arc(
                    x_center - arc_radius,
                    y_center - arc_radius,
                    x_center + arc_radius,
                    y_center + arc_radius,
                    fill="white",
                    style=tk.PIESLICE,
                    tags="arc",
                    start=left_angle,
                    extent=right_angle - left_angle,
                )
                self._draw_group_type_card(feature, padded_bbox, x)

    def _draw_node(self, feature, x, y):
        max_width = self.MAX_NODE_WIDTH
        padding_x = 4
        padding_y = 2

        node_id = self.canvas.create_text(
            x, y, text=feature.name, tags=(f"feature_text:{feature.name}", feature.name)
        )
        bbox = self.canvas.bbox(node_id)
        width = bbox[2] - bbox[0]

        truncated = False
        if width > max_width:
            truncated = True
            truncated_name = feature.name
            while width > max_width - 10:
                self.canvas.delete(node_id)
                truncated_name = truncated_name[:-1]
                node_id = self.canvas.create_text(
                    x,
                    y,
                    text=truncated_name + "...",
                    tags=(f"feature_text:{feature.name}", feature.name),
                )
                bbox = self.canvas.bbox(node_id)
                width = bbox[2] - bbox[0]

        padded_bbox = (
            bbox[0] - padding_x,
            bbox[1] - padding_y,
            bbox[2] + padding_x,
            bbox[3] + padding_y,
        )
        rect_id = self.canvas.create_rectangle(
            padded_bbox,
            fill="lightgrey",
            tags=(f"feature_rect:{feature.name}", feature.name),
        )
        self.canvas.tag_raise(node_id, rect_id)

        # Attach tooltip to show full feature name if truncated
        if truncated:
            tooltip = ToolTip(self.canvas)

            def on_enter(event):
                tooltip_bbox = self.canvas.bbox(node_id)
                if tooltip_bbox:
                    tooltip_x, tooltip_y = (
                        tooltip_bbox[2],
                        tooltip_bbox[1],
                    )  # Position at top-right of text
                    tooltip.show_tip(feature.name, tooltip_x, tooltip_y)

            def on_leave(event):
                tooltip.hide_tip()

            self.canvas.tag_bind(node_id, "<Enter>", on_enter)
            self.canvas.tag_bind(node_id, "<Leave>", on_leave)
        return node_id, padded_bbox

    def _draw_feat_instance_card(
        self, feature, feature_instance_card_pos, padded_bbox, x
    ):
        # bbox[1] is the y-coordinate of the top side of the box
        anchor: str
        match feature_instance_card_pos:
            case "right":
                anchor = tk.W
                feature_instance_x = x + 4
            case "left":
                anchor = tk.E
                feature_instance_x = x - 4
            case _:
                anchor = tk.CENTER
                feature_instance_x = x
        feature_instance_y = padded_bbox[1] - 10
        # TODO: The brackets don't look nice
        self.canvas.create_text(
            feature_instance_x,
            feature_instance_y,
            text=cardinality_to_display_str(feature.instance_cardinality, "<", ">"),
            font=self.CARDINALITY_FONT,
            tags=f"{feature.name}_feature_instance",
            anchor=anchor,
        )

    def _draw_collapse_expand_button(self, feature, padded_bbox, y):
        expanded = self.expanded_features.get(id(feature), True)
        button_text, button_color = ("-", "firebrick") if expanded else ("+", "green")
        button_id = self.canvas.create_text(
            padded_bbox[2] + 10,
            y,
            text=button_text,
            tags="button",
            font=Font(weight="bold"),
            fill=button_color,
        )
        self.canvas.tag_bind(
            button_id,
            self.click_handler.left_click(),
            lambda event, f=feature: self._toggle_children(event, f),
        )

    def _draw_group_instance_card(self, feature, new_x, new_y, padded_bbox, x, y):
        # Calculate text position for group instance cardinality with linear interpolation
        slope = (new_x - x) / (new_y - 10 - (y + 10))
        group_instance_y = padded_bbox[3] + 10
        group_instance_x = x + slope * (group_instance_y - (y + 10)) + 7
        # anchor w means west, so the left side of the text is placed at the specified position
        self.canvas.create_text(
            group_instance_x,
            group_instance_y,
            text=cardinality_to_display_str(
                feature.group_instance_cardinality, "<", ">"
            ),
            font=self.CARDINALITY_FONT,
            tags=f"{feature.name}_group_instance",
            anchor=tk.W,
        )

    def _draw_group_type_card(self, feature, padded_bbox, x):
        # bbox[3] is the y-coordinate of the bottom of the text box
        group_type_y = padded_bbox[3] + 20
        self.canvas.create_text(
            x,
            group_type_y,
            text=cardinality_to_display_str(feature.group_type_cardinality, "[", "]"),
            font=self.CARDINALITY_FONT,
            tags=f"{feature.name}_group_type",
        )

    def _on_right_click_node(self, event, feature):
        menu = tk.Menu(self.tk_root, tearoff=0)
        menu.add_command(
            label="Add Child", command=lambda: self.editor.add_feature(feature)
        )
        menu.add_command(
            label="Edit Feature", command=lambda: self.editor.edit_feature(feature)
        )
        menu.add_command(
            label="Delete Feature", command=lambda: self.editor.delete_feature(feature)
        )
        menu.add_command(
            label="Add Constraint", command=lambda: self.add_constraint(feature)
        )
        menu.post(event.x_root, event.y_root)

    def _on_left_click_node(self, event, feature: Feature):
        self._highlight_feature(feature)

    def _highlight_feature(self, feature):
        self._cancel_highlight()
        node_id = self.canvas.find_withtag(f"feature_rect:{feature.name}")
        if node_id:
            self.canvas.itemconfig(node_id[0], fill="lightblue")
            self.currently_highlighted_feature = feature

    def _cancel_highlight(self):
        if self.currently_highlighted_feature:
            previous_node = self.canvas.find_withtag(
                f"feature_rect:{self.currently_highlighted_feature.name}"
            )
            if previous_node:
                self.canvas.itemconfig(previous_node[0], fill="lightgrey")
            self.currently_highlighted_feature = None

    def _toggle_children(self, event, feature):
        self.expanded_features[id(feature)] = not self.expanded_features.get(
            id(feature), True
        )
        self.editor.update_model_state()

    def add_constraint(self, feature):
        """
        Start the process of adding a constraint between features.

        Args:
            feature (Feature): The feature to start the constraint from.
        """
        self._highlight_feature(feature)

        def on_canvas_click(event):
            clicked_item = self.canvas.find_withtag("current")
            if not clicked_item:
                messagebox.showerror("Selection Error", "Please click on a feature.")
                return

            clicked_tags = self.canvas.gettags(clicked_item[0])
            second_feature_name = next(
                (
                    tag
                    for tag in clicked_tags
                    if tag in (feat.name for feat in self.editor.cfm.features)
                ),
                None,
            )
            second_feature = next(
                (f for f in self.editor.cfm.features if f.name == second_feature_name),
                None,
            )

            if not second_feature:
                messagebox.showerror("Selection Error", "Please click on a feature.")
                return

            self.cancel_add_constraint()
            self.editor.constraints.constraint_dialog(
                initial_first_feature=feature, initial_second_feature=second_feature
            )

        self.info_label = self.canvas.create_text(
            400,
            15,
            text="Click on the second feature to define the constraint.",
            fill="black",
            font=("Arial", 12),
        )
        cancel_button = ttk.Button(
            self.tk_root, text="Cancel", command=self.cancel_add_constraint
        )
        self.cancel_button_window = self.canvas.create_window(
            650, 15, window=cancel_button
        )
        self.canvas.bind(self.click_handler.left_click(), on_canvas_click)

    def cancel_add_constraint(self):
        """
        Cancel the process of adding a constraint.
        """
        self.canvas.delete(self.info_label)
        self.canvas.delete(self.cancel_button_window)
        self.canvas.unbind(self.click_handler.left_click())
        self._cancel_highlight()

    def add_expanded_feature(self, feature: Feature):
        """
        Mark a feature as expanded.

        Args:
            feature (Feature): The feature to mark as expanded.
        """
        self.expanded_features[id(feature)] = True
