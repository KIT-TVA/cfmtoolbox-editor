from unittest.mock import Mock, MagicMock
import pytest
from tkinter import Menu
from cfmtoolbox_editor.cfm_menubar import CFMMenuBar


@pytest.fixture
def setup_menubar():
    root = MagicMock()
    editor = MagicMock()
    editor.shortcut_manager.accelerators = {
        "SAVE": "Ctrl+S",
        "RESET": "Ctrl+R",
        "UNDO": "Ctrl+Z",
        "REDO": "Ctrl+Y",
        "ADD_FEATURE": "Ctrl+N",
        "ADD_CONSTRAINT": "Ctrl+K",
        "EDIT_FEATURE": "Ctrl+E",
        "DELETE_FEATURE": "Del",
    }
    return root, editor


def test_menubar_initialization(setup_menubar):
    root, editor = setup_menubar
    menubar = CFMMenuBar(root, editor)
    assert isinstance(menubar.menubar, Menu)
    assert menubar.root == root
    assert menubar.editor == editor


def test_file_menu_creation(setup_menubar):
    root, editor = setup_menubar
    menubar = CFMMenuBar(root, editor)
    file_menu = menubar._create_file_menu()
    assert isinstance(file_menu, Menu)


def test_edit_menu_creation(setup_menubar):
    root, editor = setup_menubar
    menubar = CFMMenuBar(root, editor)
    edit_menu = menubar._create_edit_menu()
    assert isinstance(edit_menu, Menu)


def test_command_execution_without_feature(setup_menubar):
    root, editor = setup_menubar
    menubar = CFMMenuBar(root, editor)
    editor.currently_highlighted_feature = None

    # Test Save command (no feature required)
    menubar._add_menu_command(menubar.menubar, "Save", editor._save_model, "SAVE")
    editor._save_model.assert_not_called()


def test_command_execution_with_feature(setup_menubar):
    root, editor = setup_menubar
    menubar = CFMMenuBar(root, editor)
    editor.currently_highlighted_feature = Mock()

    # Test Add Feature command (feature required)
    menubar._add_menu_command(
        menubar.menubar,
        "Add Feature",
        lambda: editor.add_feature(editor.currently_highlighted_feature),
        "ADD_FEATURE",
    )
    editor.add_feature.assert_not_called()
