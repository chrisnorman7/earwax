"""Test editors."""

import re
from typing import Optional

from earwax import Editor, Game, TextValidator
from pyglet.clock import schedule_once
from pyglet.window import Window, key
from pytest import raises


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


def test_validator_class() -> None:
    """Test the EditorValidtor class initialises properly."""

    def f(text: str) -> Optional[str]:
        return None

    v: TextValidator = TextValidator(f)
    assert v.func is f


def test_validate(game: Game, window: Window) -> None:
    """Ensure that text is validated properly."""
    e: Editor = Editor(game, validator=TextValidator.not_empty())

    @e.event
    def on_submit(text: str) -> None:
        e.text = "Worked."
        window.close()

    def f(dt: float) -> None:
        e.submit()
        assert e.text == ""
        e.text = "Testing"
        e.submit()

    @game.event
    def before_run() -> None:
        schedule_once(f, 0.2)

    game.run(window, initial_level=e)
    assert e.text == "Worked."


def test_regexp() -> None:
    """Test the regexp constructor."""
    v: TextValidator = TextValidator.regexp(re.compile("1234"))
    assert v.func("1234") is None
    assert v.func("5678") == "Invalid value: 5678."


def test_not_empty() -> None:
    """Test the not_empty constructor."""
    v: TextValidator = TextValidator.not_empty()
    assert v.func("") == "You must supply a value."
    assert v.func("Hello world.") is None


def test_float() -> None:
    """Test the float constructor."""
    v: TextValidator = TextValidator.float()
    assert v.func("0.5") is None
    assert v.func("test") == "Invalid decimal: test."


def test_int() -> None:
    """Test the int constructor."""
    v: TextValidator = TextValidator.int()
    assert v.func("1234") is None
    assert v.func("test") == "Invalid number: test."
