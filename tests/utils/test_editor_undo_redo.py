import pytest
from cfmtoolbox import Feature, CFM, Cardinality, Interval, Constraint
from cfmtoolbox_editor.utils.cfm_editor_undo_redo import UndoRedoManager


@pytest.fixture
def sandwich_cfm():
    # Root feature mit allen erforderlichen Argumenten
    sandwich = Feature(
        name="sandwich",
        instance_cardinality=Cardinality([Interval(1, 1)]),
        group_type_cardinality=Cardinality([Interval(2, 7)]),
        group_instance_cardinality=Cardinality([Interval(2, 7)]),
        parent=None,
        children=[],
    )

    # Bread feature
    bread = Feature(
        name="bread",
        instance_cardinality=Cardinality([Interval(2, 2)]),
        group_type_cardinality=Cardinality([Interval(1, 1)]),  # alternative
        group_instance_cardinality=Cardinality([Interval(1, 1)]),
        parent=sandwich,
        children=[],
    )

    # Bread types
    sourdough = Feature(
        name="sourdough",
        instance_cardinality=Cardinality([Interval(0, 1)]),
        group_type_cardinality=Cardinality([Interval(0, 0)]),
        group_instance_cardinality=Cardinality([Interval(0, 0)]),
        parent=bread,
        children=[],
    )

    wheat = Feature(
        name="wheat",
        instance_cardinality=Cardinality([Interval(0, 1)]),
        group_type_cardinality=Cardinality([Interval(0, 0)]),
        group_instance_cardinality=Cardinality([Interval(0, 0)]),
        parent=bread,
        children=[],
    )

    veggies = Feature(
        name="veggies",
        instance_cardinality=Cardinality([Interval(0, 1)]),
        group_type_cardinality=Cardinality([Interval(1, 2)]),  # or
        group_instance_cardinality=Cardinality([Interval(1, 2)]),
        parent=sandwich,
        children=[],
    )

    # Veggies types
    lettuce = Feature(
        name="lettuce",
        instance_cardinality=Cardinality([Interval(0, None)]),
        group_type_cardinality=Cardinality([Interval(0, 0)]),
        group_instance_cardinality=Cardinality([Interval(0, 0)]),
        parent=veggies,
        children=[],
    )

    # Cheese feature mit Kindern
    cheesemix = Feature(
        name="Cheesemix",
        instance_cardinality=Cardinality([Interval(2, 4)]),
        group_type_cardinality=Cardinality([Interval(1, 3)]),  # or
        group_instance_cardinality=Cardinality([Interval(1, 3)]),
        parent=sandwich,
        children=[],
    )

    veggies.children = [lettuce]
    sandwich.children = [bread, cheesemix, veggies]
    bread.children = [sourdough, wheat]

    constraints = [
        Constraint(
            first_feature=wheat,
            first_cardinality=Cardinality([Interval(1, None)]),
            second_feature=lettuce,
            second_cardinality=Cardinality([Interval(1, None)]),
            require=True,  # Hinzugefügt: require Parameter
        ),
        Constraint(
            first_feature=cheesemix,
            first_cardinality=Cardinality([Interval(1, None)]),
            second_feature=sourdough,
            second_cardinality=Cardinality([Interval(1, None)]),
            require=True,  # Hinzugefügt: require Parameter
        ),
    ]

    return CFM(root=sandwich, constraints=constraints)


class TestUndoRedoManager:
    """Test class for UndoRedoManager"""

    def test_add_state_with_sandwich_cfm(self, sandwich_cfm):
        """Test adding states with sandwich CFM"""
        self.sandwich_cfm = sandwich_cfm
        manager = UndoRedoManager()

        manager.add_state(self.sandwich_cfm)

        # Verify the state is added
        assert len(manager.undo_stack) == 1
        assert len(manager.redo_stack) == 0

    def test_undo_on_initial_sandwich_cfm(self, sandwich_cfm):
        """Test undo on the initial state of sandwich CFM"""
        self.sandwich_cfm = sandwich_cfm
        manager = UndoRedoManager()

        manager.add_state(self.sandwich_cfm)

        result = manager.undo()
        assert result is None  # Undo should return None for the initial state.

    def test_redo_on_empty_sandwich_cfm(self, sandwich_cfm):
        """Test redo on an empty redo stack with sandwich CFM"""
        self.sandwich_cfm = sandwich_cfm
        manager = UndoRedoManager()

        manager.add_state(self.sandwich_cfm)

        result = manager.redo()
        assert result is None  # Redo should return None as there is no undone state.

    def test_undo_redo_multiple_changes_sandwich_cfm(self, sandwich_cfm):
        """Test undo and redo for multiple changes in sandwich CFM"""
        self.sandwich_cfm = sandwich_cfm
        manager = UndoRedoManager()

        # Initial state
        manager.add_state(self.sandwich_cfm)

        # Change 1: Modify bread cardinality
        bread = self.sandwich_cfm.root.children[0]
        bread.instance_cardinality.intervals[0].upper = 3
        manager.add_state(self.sandwich_cfm)

        # Change 2: Add a new feature
        new_feature = Feature(
            name="Cheese",
            instance_cardinality=Cardinality([Interval(1, 1)]),
            group_type_cardinality=Cardinality([Interval(1, 1)]),
            group_instance_cardinality=Cardinality([Interval(1, 1)]),
            parent=self.sandwich_cfm.root,
            children=[],
        )
        self.sandwich_cfm.root.children.append(new_feature)
        manager.add_state(self.sandwich_cfm)

        # Undo both changes
        assert manager.undo().root.children[-1].name != "Cheese"  # Undo addition
        assert (
            manager.undo().root.children[0].instance_cardinality.intervals[0].upper == 2
        )  # Undo cardinality change

        # Redo both changes
        assert (
            manager.redo().root.children[0].instance_cardinality.intervals[0].upper == 3
        )  # Redo cardinality change
        assert manager.redo().root.children[-1].name == "Cheese"  # Redo addition

    def test_clear_redo_stack_on_new_state_sandwich_cfm(self, sandwich_cfm):
        """Test that adding a new state after undo clears the redo stack"""
        self.sandwich_cfm = sandwich_cfm
        manager = UndoRedoManager()

        # Initial state
        manager.add_state(self.sandwich_cfm)

        # Change: Modify bread cardinality
        bread = self.sandwich_cfm.root.children[0]
        bread.instance_cardinality.intervals[0].max = 3
        manager.add_state(self.sandwich_cfm)

        # Undo the change
        self.sandwich_cfm = manager.undo()

        # Add a new change
        self.sandwich_cfm.root.name = "ModifiedSandwich"
        manager.add_state(self.sandwich_cfm)

        # Verify redo stack is cleared
        assert len(manager.redo_stack) == 0
        assert manager.undo().root.name == "sandwich"  # Undo the new change

    def test_no_effect_on_single_state_undo(self, sandwich_cfm):
        """Test undo with only a single state in the undo stack"""
        self.sandwich_cfm = sandwich_cfm
        manager = UndoRedoManager()

        # Add initial state
        manager.add_state(self.sandwich_cfm)

        # Try undo
        result = manager.undo()
        assert result is None  # Undo should not do anything

    def test_large_changes_sandwich_cfm(self, sandwich_cfm):
        """Test undo/redo behavior with significant changes in sandwich CFM"""
        self.sandwich_cfm = sandwich_cfm
        manager = UndoRedoManager()

        # Add initial state
        manager.add_state(self.sandwich_cfm)

        prev_length = len(self.sandwich_cfm.root.children)

        # Add multiple features
        for i in range(10):
            self.sandwich_cfm.root.children.append(
                Feature(
                    name=f"ExtraFeature{i}",
                    instance_cardinality=Cardinality([Interval(1, 1)]),
                    group_type_cardinality=Cardinality([Interval(1, 1)]),
                    group_instance_cardinality=Cardinality([Interval(1, 1)]),
                    parent=self.sandwich_cfm.root,
                    children=[],
                )
            )
            manager.add_state(self.sandwich_cfm)

        # Undo all changes
        for _ in range(10):
            self.sandwich_cfm = manager.undo()

        assert len(self.sandwich_cfm.root.children) == prev_length

        # Redo all changes
        for _ in range(10):
            self.sandwich_cfm = manager.redo()

        assert len(self.sandwich_cfm.root.children) == prev_length + 10

    def test_alternating_undo_redo_cycles_sandwich_cfm(self, sandwich_cfm):
        """Test alternating undo and redo cycles in sandwich CFM"""
        self.sandwich_cfm = sandwich_cfm
        manager = UndoRedoManager()

        # Add initial state
        manager.add_state(self.sandwich_cfm)

        prev_length = len(self.sandwich_cfm.root.children)

        # Add multiple features
        for i in range(5):
            self.sandwich_cfm.root.children.append(
                Feature(
                    name=f"ExtraFeature{i}",
                    instance_cardinality=Cardinality([Interval(1, 1)]),
                    group_type_cardinality=Cardinality([Interval(1, 1)]),
                    group_instance_cardinality=Cardinality([Interval(1, 1)]),
                    parent=self.sandwich_cfm.root,
                    children=[],
                )
            )
            manager.add_state(self.sandwich_cfm)

        # Perform alternating undo and redo cycles
        for _ in range(5):
            self.sandwich_cfm = manager.undo()
            assert len(self.sandwich_cfm.root.children) == prev_length + 4

            self.sandwich_cfm = manager.redo()
            assert len(self.sandwich_cfm.root.children) == prev_length + 5

    def test_delete_cheesemix_undo_redo_add_child_undo(self, sandwich_cfm):
        """Test deleting Cheesemix, undo, redo, undo, adding a child, and undo"""
        self.sandwich_cfm = sandwich_cfm
        manager = UndoRedoManager()

        # Add initial state
        manager.add_state(self.sandwich_cfm)

        # Step 1: Delete Cheesemix
        cheesemix = self.sandwich_cfm.root.children.pop(1)
        manager.add_state(self.sandwich_cfm)
        assert len(self.sandwich_cfm.root.children) == 2
        assert all(
            child.name != "Cheesemix" for child in self.sandwich_cfm.root.children
        )

        # Step 2: Undo the deletion
        self.sandwich_cfm = manager.undo()
        assert len(self.sandwich_cfm.root.children) == 3
        assert any(
            child.name == "Cheesemix" for child in self.sandwich_cfm.root.children
        )

        # Step 3: Redo the deletion
        self.sandwich_cfm = manager.redo()
        assert len(self.sandwich_cfm.root.children) == 2
        assert all(
            child.name != "Cheesemix" for child in self.sandwich_cfm.root.children
        )

        # Step 4: Undo the deletion again
        self.sandwich_cfm = manager.undo()
        assert len(self.sandwich_cfm.root.children) == 3
        assert any(
            child.name == "Cheesemix" for child in self.sandwich_cfm.root.children
        )

        # Step 5: Add a child to Cheesemix
        cheesemix = next(
            child
            for child in self.sandwich_cfm.root.children
            if child.name == "Cheesemix"
        )
        new_child = Feature(
            name="NewChild",
            instance_cardinality=Cardinality([Interval(1, 1)]),
            group_type_cardinality=Cardinality([Interval(1, 1)]),
            group_instance_cardinality=Cardinality([Interval(1, 1)]),
            parent=cheesemix,
            children=[],
        )
        cheesemix.children.append(new_child)
        manager.add_state(self.sandwich_cfm)
        assert len(cheesemix.children) == 1

        # Step 6: Undo the addition of the child
        self.sandwich_cfm = manager.undo()
        cheesemix = next(
            child
            for child in self.sandwich_cfm.root.children
            if child.name == "Cheesemix"
        )
        assert len(cheesemix.children) == 0
