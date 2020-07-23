"""Provides the Editor class."""

from typing import Callable, Dict, Optional

from attr import Factory, attrib, attrs
from pyglet.window import key

from .speech import tts

MotionFunctionType = Callable[[], None]
MotionsType = Dict[int, MotionFunctionType]


@attrs(auto_attribs=True)
class Editor:
    """A basic text editor."""

    # The function to be called with the text in this editor when the enter key
    # is pressed.
    func: Callable[[str], None]

    # The contents of this editor.
    text: str = Factory(str)

    # The position of the cursor (None means text should be appended).
    cursor_position: Optional[int] = Factory(type(None))

    # Whether or not it should be possible to dismiss this editor.
    dismissible: bool = Factory(lambda: True)

    # The defined motion events. To define more, use the motion decorator.
    motions: MotionsType = attrib(Factory(dict), init=False)

    def __attrs_post_init__(self) -> None:
        self.motion(key.MOTION_BACKSPACE)(self.motion_backspace)
        self.motion(key.MOTION_DELETE)(self.motion_delete)
        self.motion(key.MOTION_LEFT)(self.motion_left)
        self.motion(key.MOTION_RIGHT)(self.motion_right)
        self.motion(key.MOTION_BEGINNING_OF_LINE)(self.beginning_of_line)
        self.motion(key.MOTION_END_OF_LINE)(self.end_of_line)
        self.motion(key.MOTION_UP)(self.motion_up)
        self.motion(key.MOTION_DOWN)(self.motion_down)

    def submit(self) -> None:
        """Submit the text in this control to self.func."""
        return self.func(self.text)

    def on_text(self, text: str) -> None:
        """Text has been entered.

        If the cursor is at the end of the line, append the text. Otherwise,
        insert it."""
        if self.cursor_position is None:
            self.text += text
        else:
            self.text = self.text[:self.cursor_position] + text +\
                self.text[self.cursor_position:]
        self.echo(text)

    def on_text_motion(self, motion: int) -> None:
        """Handle a motion event."""
        if motion in self.motions:
            return self.motions[motion]()
        raise NotImplementedError(key.motion_string(motion))

    def echo(self, text: str):
        """Output entered text. Overridden by PasswordEditor, to speak "*"."""
        if text == ' ':
            text = 'space'
        tts.speak(text)

    def echo_current_character(self) -> None:
        """Echo the current character."""
        if self.cursor_position is None:
            return self.echo('')
        self.echo(self.text[self.cursor_position])

    def set_cursor_position(self, pos: Optional[int]) -> None:
        """If pos is None, then the cursor will be at the end of the line.
        Otherwise, pos should be an integer between 0 and len(self.text) -
        1."""
        if pos is not None and pos >= len(self.text):
            pos = None
        self.cursor_position = pos
        if pos is None:
            return self.echo('')
        self.echo_current_character()

    def clear(self) -> None:
        """Clear this editor."""
        self.text = ''
        self.set_cursor_position(None)

    def motion(
        self, motion: int
    ) -> Callable[[MotionFunctionType], MotionFunctionType]:
        """A decorator to add a handler to self.motions."""

        def inner(func: MotionFunctionType) -> MotionFunctionType:
            self.motions[motion] = func
            return func

        return inner

    def motion_backspace(self) -> None:
        """Delete the previous character."""
        if self.cursor_position is None:
            if self.text == '':
                self.echo('No text to delete.')
            else:
                self.echo(self.text[-1])
                self.text = self.text[:-1]
        elif self.cursor_position == 0:
            self.echo('')
        else:
            self.set_cursor_position(self.cursor_position - 1)
            self.text = self.text[:self.cursor_position] + self.text[
                self.cursor_position + 1:
            ]

    def motion_delete(self) -> None:
        """Delete the character under the cursor."""
        if self.cursor_position is None:
            return self.echo('')
        self.text = self.text[:self.cursor_position] + self.text[
            self.cursor_position + 1:
        ]
        self.echo_current_character()

    def motion_left(self) -> None:
        """Move left in the editor."""
        if self.cursor_position is None:
            if self.text == '':
                return self.echo('')
            self.set_cursor_position(len(self.text) - 1)
        else:
            self.set_cursor_position(max(0, self.cursor_position - 1))

    def motion_right(self) -> None:
        """Move right in the editor."""
        if self.cursor_position is None:
            return self.echo('')
        self.set_cursor_position(self.cursor_position + 1)

    def beginning_of_line(self) -> None:
        """Move to the start of the current line."""
        self.set_cursor_position(0)

    def end_of_line(self) -> None:
        """Move to the end of the line."""
        self.set_cursor_position(None)

    def motion_up(self) -> None:
        """Since we're not bothering with multiline text fields at this stage,
        just move the cursor to the start of the line, and read the whole
        thing."""
        self.cursor_position = 0
        self.echo(self.text)

    def motion_down(self) -> None:
        """Since we're not bothering with multiline text fields at this stage,
        just move the cursor to the end of the line, and read the whole
        thing."""
        self.cursor_position = None
        self.echo(self.text)
