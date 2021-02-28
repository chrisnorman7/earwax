"""Test the various dialogue classes."""

from pathlib import Path

from pytest import raises

from earwax import DialogueLine, DialogueTree


def test_dialogue_line_init(dialogue_tree: DialogueTree) -> None:
    """Test initialisation."""
    l: DialogueLine = DialogueLine(
        dialogue_tree, text="Hello world.", sound=Path("sound.wav")
    )
    assert dialogue_tree.children == [l]
    assert l.responses == []
    assert l.parent is dialogue_tree
    assert l.text == "Hello world."
    assert l.sound == Path("sound.wav")
    assert l.can_show is None
    assert l.on_activate is None
    with raises(RuntimeError):
        DialogueLine(dialogue_tree)


def test_dialogue_tree_init(dialogue_tree: DialogueTree) -> None:
    """Test initialisation."""
    assert isinstance(dialogue_tree, DialogueTree)
    assert dialogue_tree.children == []


def test_get_children(dialogue_tree: DialogueTree) -> None:
    """Test the get_children method."""
    l1: DialogueLine = DialogueLine(dialogue_tree, text="Test 1")
    l2: DialogueLine = DialogueLine(
        dialogue_tree, text="Test2", can_show=lambda: False
    )
    assert dialogue_tree.children == [l1, l2]
    assert dialogue_tree.get_children() == [l1]
    l2.can_show = lambda: True
    assert dialogue_tree.get_children() == [l1, l2]
