"""Test the various dialogue classes."""

from pathlib import Path

from pytest import raises

from earwax import DialogueLine, DialogueTree


def test_dialogue_line() -> None:
    """Test initialisation."""
    t: DialogueTree = DialogueTree()
    l: DialogueLine = DialogueLine(
        t, text='Hello world.', sound=Path('sound.wav')
    )
    assert t.children == [l]
    assert l.responses == []
    assert l.parent is t
    assert l.text == 'Hello world.'
    assert l.sound == Path('sound.wav')
    assert l.can_show is None
    assert l.on_activate is None
    with raises(RuntimeError):
        DialogueLine(t)


def test_dialogue_tree_init() -> None:
    """Test initialisation."""
    t: DialogueTree = DialogueTree()
    assert t.children == []
