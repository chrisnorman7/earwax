"""Test editors."""

from pyglet.clock import schedule_once
from pyglet.window import Window, key
from pytest import raises

from earwax import Editor, Game


class Works(Exception):
    pass


def test_init(editor: Editor) -> None:
    assert editor.text == ''
    assert editor.cursor_position is None
    assert editor.dismissible is True
    assert editor.vertical_position == -1


def test_submit(game: Game) -> None:
    e = Editor(game, text='test')

    @e.event
    def on_submit(text: str) -> None:
        raise Works(text)

    game.push_level(e)
    with raises(Works) as exc:
        game.press_key(key.RETURN, 0, string='\n')
    assert exc.value.args == (e.text,)


def test_on_text(game: Game, editor: Editor, window: Window) -> None:
    def inner(dt: float) -> None:
        window.dispatch_event('on_text', 'hello')
        assert editor.text == 'hello'
        window.dispatch_event('on_text', 'world')
        assert editor.text == 'helloworld'
        editor.set_cursor_position(5)
        window.dispatch_event('on_text', ' ')
        assert editor.text == 'hello world'
        window.close()

    @game.event
    def before_run() -> None:
        schedule_once(inner, 1.0)

    game.run(window, initial_level=editor)


def test_on_text_motion(game: Game, editor: Editor) -> None:
    editor.text = 'hello world'
    game.push_level(editor)
    editor.on_text_motion(key.MOTION_BACKSPACE)
    assert editor.text == 'hello worl'
    editor.on_text_motion(key.MOTION_BEGINNING_OF_LINE)
    assert editor.cursor_position == 0
    editor.on_text_motion(key.MOTION_DELETE)
    assert editor.text == 'ello worl'
    editor.on_text_motion(key.MOTION_END_OF_LINE)
    assert editor.cursor_position is None
