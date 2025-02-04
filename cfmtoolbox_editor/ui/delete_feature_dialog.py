import tkinter as tk
from tkinter import messagebox

from cfmtoolbox import Cardinality, Feature

from cfmtoolbox_editor.utils.cfm_utils import (
    derive_parent_group_cards_for_one_child,
    derive_parent_group_cards_for_multiple_children,
)


class DeleteFeatureDialog:
    def __init__(
        self,
        parent_widget,
        feature: Feature,
        cfm,
        update_model_state_callback,
        show_feature_dialog_callback,
    ):
        """
        Dialog for deleting a feature. Allows the user to either delete the subtree or transfer children to the parent.

        Args:
            parent_widget: The parent Tk widget (e.g., root window).
            feature (Feature): The feature to delete.
            cfm: The CFM model, containing constraints and features.
            update_model_state_callback (callable): Function to update the model state after modifications.
            show_feature_dialog_callback (callable): Function to open the feature dialog for editing.
        """
        self.parent_widget = parent_widget
        self.feature = feature
        self.cfm = cfm
        self.update_model_state = update_model_state_callback
        self.show_feature_dialog = show_feature_dialog_callback
        self.dialog = None
        self.result = None

        self.create_dialog()

    def create_dialog(self):
        """Creates and displays the dialog."""
        self.dialog = tk.Toplevel(self.parent_widget)
        self.dialog.title("Delete Feature")
        self.dialog.geometry("300x150")
        self.dialog.transient(self.parent_widget)
        self.dialog.grab_set()

        label = tk.Label(
            self.dialog,
            text=(
                f"Choose the delete method for feature {self.feature.name}. "
                f"Delete subtree will also delete all descendants, transfer will attach them to their grandparent."
            ),
            wraplength=280,
            justify="left",
        )
        label.pack(pady=10)

        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=10)

        tk.Button(
            button_frame, text="Delete subtree", command=lambda: self.submit(True)
        ).pack(side="left", padx=5)
        tk.Button(
            button_frame, text="Transfer", command=lambda: self.submit(False)
        ).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(
            side="left", padx=5
        )

        self.dialog.wait_window(self.dialog)

    def submit(self, delete_subtree: bool):
        """Handles the deletion logic based on the user's choice."""
        parent = self.feature.parent
        if not parent:
            messagebox.showerror("Error", "Cannot delete root feature.")
            self.dialog.destroy()
            return

        former_number_of_children = len(parent.children)

        if delete_subtree:
            # Remove all constraints that involve children of the feature
            self.cfm.constraints = [
                c
                for c in self.cfm.constraints
                if c.first_feature not in self.feature.children
                and c.second_feature not in self.feature.children
            ]
        else:
            # Transfer children to the parent
            index = parent.children.index(self.feature)
            for child in reversed(self.feature.children):
                parent.children.insert(index, child)
                child.parent = parent

        parent.children.remove(self.feature)

        # Remove constraints involving the feature itself
        self.cfm.constraints = [
            c
            for c in self.cfm.constraints
            if c.first_feature != self.feature and c.second_feature != self.feature
        ]

        group_created = False
        if len(parent.children) == 0:
            parent.group_type_cardinality, parent.group_instance_cardinality = (
                Cardinality([]),
                Cardinality([]),
            )
        elif len(parent.children) == 1:
            parent.group_type_cardinality, parent.group_instance_cardinality = (
                derive_parent_group_cards_for_one_child(
                    parent.children[0].instance_cardinality
                )
            )
        elif len(parent.children) == 2 and former_number_of_children < 2:
            parent.group_type_cardinality, parent.group_instance_cardinality = (
                derive_parent_group_cards_for_multiple_children(
                    [child.instance_cardinality for child in parent.children]
                )
            )
            group_created = True

        self.update_model_state()
        self.dialog.destroy()

        if group_created:
            messagebox.showinfo(
                "Group Created",
                "A new group was created. You can edit its cardinalities now.",
            )
            self.show_feature_dialog(feature=parent)
