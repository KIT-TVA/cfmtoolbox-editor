from tkinter import messagebox
from tkinter import Toplevel, Label, Entry, StringVar, Button

from cfmtoolbox import Cardinality, Feature, Interval

from cfmtoolbox_editor.utils.cfm_utils import (
    derive_parent_group_cards_for_multiple_children,
    derive_parent_group_cards_for_one_child,
    edit_str_to_cardinality,
    cardinality_to_edit_str,
)


class FeatureDialog:
    """
    A dialog for adding or editing features in a feature model.

    This dialog allows users to input or edit a feature's name, cardinality, and group cardinalities (if applicable).
    It supports validation for unique names and correct cardinality formats. Automatically adjusts parent group
    cardinalities when necessary and provides feedback if a new group is created.

    Attributes:
        parent: The Tk root window or parent widget.
        cfm: The feature model containing the list of features.
        expanded_features: Dictionary of feature IDs to expanded/collapsed states.
        update_model_state_callback: Callback to update the model state.
        show_feature_dialog_callback: Callback to reopen the dialog for a parent feature.
        parent_feature: The parent feature for the new feature (if adding).
        feature: The feature being edited (if applicable).
    """

    def __init__(
        self,
        parent_widget,
        cfm,
        expanded_features,
        update_model_state_callback,
        show_feature_dialog_callback,
        parent_feature=None,
        feature=None,
    ):
        self.parent_widget = parent_widget  # The Tk root window or parent widget
        self.cfm = cfm
        self.expanded_features = expanded_features
        self.update_model_state_callback = update_model_state_callback
        self.show_feature_dialog_callback = show_feature_dialog_callback
        self.parent_feature = parent_feature
        self.feature = feature

        self.is_edit = feature is not None
        self.is_group = feature is not None and len(feature.children) > 1
        self.is_only_child = (
            feature is not None and feature.parent and len(feature.parent.children) == 1
        )

        self.dialog = Toplevel(self.parent_widget)
        self.dialog.title("Edit Feature" if self.is_edit else "Add Feature")
        self.dialog.transient(self.parent_widget)
        self.dialog.grab_set()

        self._create_widgets()
        self._center_window()
        self.dialog.wait_window(self.dialog)

    def _create_widgets(self):
        current_name = self.feature.name if self.feature else ""
        current_feature_card = (
            cardinality_to_edit_str(self.feature.instance_cardinality)
            if self.feature
            else ""
        )

        Label(self.dialog, text="Feature Name:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.name_var = StringVar(value=current_name)
        Entry(self.dialog, textvariable=self.name_var).grid(
            row=0, column=1, padx=5, pady=5
        )

        Label(self.dialog, text="Feature cardinality (e.g., '1,2; 5,*'):").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        self.feature_card_var = StringVar(value=current_feature_card)
        Entry(self.dialog, textvariable=self.feature_card_var).grid(
            row=1, column=1, padx=5, pady=5
        )

        if self.is_group and self.feature:
            current_group_type_card = cardinality_to_edit_str(
                self.feature.group_type_cardinality
            )
            current_group_instance_card = cardinality_to_edit_str(
                self.feature.group_instance_cardinality
            )

            Label(self.dialog, text="Group type cardinality:").grid(
                row=2, column=0, padx=5, pady=5, sticky="w"
            )
            self.group_type_card_var = StringVar(value=current_group_type_card)
            Entry(self.dialog, textvariable=self.group_type_card_var).grid(
                row=2, column=1, padx=5, pady=5
            )

            Label(self.dialog, text="Group instance cardinality:").grid(
                row=3, column=0, padx=5, pady=5, sticky="w"
            )
            self.group_instance_card_var = StringVar(value=current_group_instance_card)
            Entry(self.dialog, textvariable=self.group_instance_card_var).grid(
                row=3, column=1, padx=5, pady=5
            )

        Button(
            self.dialog,
            text="Save changes" if self.is_edit else "Add",
            command=self._on_submit,
        ).grid(row=4, column=0, columnspan=2, pady=10)

    def _center_window(self):
        self.parent_widget.update_idletasks()
        main_window_x = self.parent_widget.winfo_x()
        main_window_y = self.parent_widget.winfo_y()
        main_window_width = self.parent_widget.winfo_width()
        main_window_height = self.parent_widget.winfo_height()

        dialog_x = (
            main_window_x
            + (main_window_width // 2)
            - (self.dialog.winfo_reqwidth() // 2)
        )
        dialog_y = (
            main_window_y
            + (main_window_height // 2)
            - (self.dialog.winfo_reqheight() // 2)
        )

        self.dialog.geometry(f"+{dialog_x}+{dialog_y}")

    def _on_submit(self):
        feature_name = self.name_var.get().strip()
        if not feature_name:
            messagebox.showerror("Input Error", "Feature name cannot be empty.")
            return

        if (feature_name in [f.name for f in self.cfm.features]) and (
            not self.is_edit or (feature_name != self.feature.name)
        ):
            messagebox.showerror("Input Error", "Feature name must be unique.")
            return

        raw_feature_card = self.feature_card_var.get().strip()
        feature_card = Cardinality([Interval(0, None)])
        if raw_feature_card:
            try:
                feature_card = edit_str_to_cardinality(raw_feature_card)
            except ValueError:
                messagebox.showerror(
                    "Input Error",
                    "Invalid feature cardinality format. Use 'min,max' or 'min,*' for intervals.",
                )
                return

        group_created = False

        if self.is_edit:
            self.feature.name = feature_name
            self.feature.instance_cardinality = feature_card
            if self.is_group:
                raw_group_type_card = self.group_type_card_var.get().strip()
                raw_group_instance_card = self.group_instance_card_var.get().strip()
                try:
                    group_type_card = edit_str_to_cardinality(raw_group_type_card)
                except ValueError:
                    messagebox.showerror(
                        "Input Error",
                        "Invalid group type cardinality format. Use 'min,max' or 'min,*' for intervals.",
                    )
                    return
                try:
                    group_instance_card = edit_str_to_cardinality(
                        raw_group_instance_card
                    )
                except ValueError:
                    messagebox.showerror(
                        "Input Error",
                        "Invalid group instance cardinality format. Use 'min,max' or 'min,*' for intervals.",
                    )
                    return
                self.feature.group_type_cardinality = group_type_card
                self.feature.group_instance_cardinality = group_instance_card
            if self.is_only_child:
                (
                    self.feature.parent.group_type_cardinality,
                    self.feature.parent.group_instance_cardinality,
                ) = derive_parent_group_cards_for_one_child(
                    self.feature.instance_cardinality
                )
        else:
            new_feature = Feature(
                name=feature_name,
                instance_cardinality=feature_card,
                group_type_cardinality=Cardinality([]),
                group_instance_cardinality=Cardinality([]),
                parent=self.parent_feature,
                children=[],
            )
            self.expanded_features[id(new_feature)] = True
            self.parent_feature.children.append(new_feature)
            if len(self.parent_feature.children) == 1:
                (
                    self.parent_feature.group_type_cardinality,
                    self.parent_feature.group_instance_cardinality,
                ) = derive_parent_group_cards_for_one_child(feature_card)
            if len(self.parent_feature.children) == 2:
                group_created = True
                (
                    self.parent_feature.group_type_cardinality,
                    self.parent_feature.group_instance_cardinality,
                ) = derive_parent_group_cards_for_multiple_children(
                    [
                        child.instance_cardinality
                        for child in self.parent_feature.children
                    ]
                )

        self.update_model_state_callback()
        self.dialog.destroy()
        if group_created:
            messagebox.showinfo(
                "Group Created",
                "A new group was created. You can edit its cardinalities now.",
            )
            self.show_feature_dialog_callback(feature=self.parent_feature)
