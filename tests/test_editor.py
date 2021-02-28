"""Test editors."""

from pyglet.clock import schedule_once
from pyglet.window import Window, key
from pytest import raises

from earwax import Editor, Game


class Works(Exception):
    """Test worked."""


def test_init(editor: Editor) -> None:
    """Test initialisation."""
    assert editor.text == ""
    assert editor.cursor_position is None
    assert editor.dismissible is True
    assert editor.vertical_position is None


def test_submit(game: Game) -> None:
    """Test that editors submit properly."""
    e = Editor(game, text="test")

    @e.event
    def on_submit(text: str) -> None:
        raise Works(text)

    game.push_level(e)
    with raises(Works) as exc:
        game.press_key(key.RETURN, 0, string="\n")
    assert exc.value.args == (e.text,)


def test_on_text(game: Game, editor: Editor, window: Window) -> None:
    """Test the on_text event."""

    def inner(dt: float) -> None:
        window.dispatch_event("on_text", "hello")
        assert editor.text == "hello"
        window.dispatch_event("on_text", "world")
        assert editor.text == "helloworld"
        editor.set_cursor_position(5)
        window.dispatch_event("on_text", " ")
        assert editor.text == "hello world"
        window.close()

    @game.event
    def before_run() -> None:
        schedule_once(inner, 1.0)

    game.run(window, initial_level=editor)


def test_on_text_motion(game: Game, editor: Editor) -> None:
    """Test the on_text_motion event."""
    editor.text = "hello world"
    game.push_level(editor)
    editor.on_text_motion(key.MOTION_BACKSPACE)
    assert editor.text == "hello worl"
    editor.on_text_motion(key.MOTION_BEGINNING_OF_LINE)
    assert editor.cursor_position == 0
    editor.on_text_motion(key.MOTION_DELETE)
    assert editor.text == "ello worl"
    editor.on_text_motion(key.MOTION_END_OF_LINE)
    assert editor.cursor_position is None


def test_hat_editing(editor: Editor) -> None:
    """Test the hat editing feature."""
    editor.text = "Test"
    editor.set_cursor_position(0)
    editor.hat_up()
    assert editor.text == "Sest"
    editor.hat_down()
    assert editor.text == "Test"
    editor.set_cursor_position(1)
    editor.hat_down()
    assert editor.text == "Tfst"
    editor.hat_up()
    assert editor.text == "Test"


def test_hat_deletes(editor: Editor) -> None:
    """Ensure text can be deleted with the hat."""
    editor.text = " Test"
    editor.set_cursor_position(0)
    assert editor.vertical_position == 0
    editor.hat_up()
    assert editor.vertical_position == -1
    assert editor.text == " Test"
    editor.hat_up()
    assert editor.text == "Test"
    editor.hat_up()
    assert editor.text == "Sest"


def test_hat_submits(editor: Editor) -> None:
    """Test that text can be submitted with the hat."""

    @editor.event
    def on_submit(text: str) -> None:
        raise Works()

    editor.hat_up()
    assert editor.vertical_position == -1
    with raises(Works):
        editor.hat_up()
