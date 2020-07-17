"""Test editors."""

from pytest import raises
from pyglet.window import key

from earwax import Editor


class Works(Exception):
    pass


def test_init():
    e = Editor(print)
    assert e.func is print
    assert e.text == ''
    assert e.cursor_position is None
    assert e.dismissible is True


def test_submit():
    def on_submit(text):
        raise Works(text)

    e = Editor(on_submit)
    e.text = 'test'
    with raises(Works) as exc:
        e.submit()
    assert exc.value.args == ('test',)


def test_on_text():
    e = Editor(None)
    e.on_text('hello')
    assert e.text == 'hello'
    e.on_text('world')
    assert e.text == 'helloworld'
    e.set_cursor_position(5)
    e.on_text(' ')
    assert e.text == 'hello world'


def test_on_text_motion():
    e = Editor(None, text='hello world')
    e.on_text_motion(key.MOTION_BACKSPACE)
    assert e.text == 'hello worl'
    e.on_text_motion(key.MOTION_BEGINNING_OF_LINE)
    assert e.cursor_position == 0
    e.on_text_motion(key.MOTION_DELETE)
    assert e.text == 'ello worl'
    e.on_text_motion(key.MOTION_END_OF_LINE)
    assert e.cursor_position is None
