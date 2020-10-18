"""Provides the Editor class."""

from typing import Callable, Optional

from attr import attrs

from .hat_directions import LEFT, RIGHT

try:
    from pyglet.window import key
except ModuleNotFoundError:
    key = None

from .action import OptionalGenerator
from .level import Level
from .mixins import DismissibleMixin


@attrs(auto_attribs=True)
class EditorBase:
    """Adds a function argument."""

    func: Callable[[str], OptionalGenerator]


@attrs(auto_attribs=True)
class Editor(Level, EditorBase, DismissibleMixin):
    """A basic text editor.

    By default, the enter key submits the contents to
    :attr:`~earwax.editor.EditorBase.func`.

    :ivar ~earwax.Editor.func: The function which should be called
        when pressing enter in an edit field.

    :ivar ~earwax.Editor.text: The text which can be edited by this object.

    :ivar ~earwax.Editor.position: The position of the cursor.
    """

    text: str = ''
    cursor_position: Optional[int] = None

    def __attrs_post_init__(self) -> None:
        """Initialise the editor."""
        self.motion(key.MOTION_BACKSPACE)(self.motion_backspace)
        self.motion(key.MOTION_DELETE)(self.motion_delete)
        self.motion(key.MOTION_LEFT)(self.motion_left)
        self.action('Left arrow', hat_direction=LEFT)(self.motion_left)
        self.motion(key.MOTION_RIGHT)(self.motion_right)
        self.action('Right arrow', hat_direction=RIGHT)(self.motion_right)
        self.motion(key.MOTION_BEGINNING_OF_LINE)(self.beginning_of_line)
        self.motion(key.MOTION_END_OF_LINE)(self.end_of_line)
        self.motion(key.MOTION_UP)(self.motion_up)
        self.motion(key.MOTION_DOWN)(self.motion_down)
        self.action('Submit text', symbol=key.RETURN)(self.submit)
        self.action('Dismiss', symbol=key.ESCAPE)(self.dismiss)
        self.action('Clear', symbol=key.U, modifiers=key.MOD_CTRL)(self.clear)

    def submit(self) -> OptionalGenerator:
        """Submit the text in this control to self.func.

        By default, this method is called when the enter key is pressed.
        """
        return self.func(self.text)

    def on_text(self, text: str) -> None:
        """Text has been entered.

        If the cursor is at the end of the line, append the text. Otherwise,
        insert it.

        :param text: The text that has been enetered.
        """
        if self.cursor_position is None:
            self.text += text
        else:
            self.text = self.text[:self.cursor_position] + text +\
                self.text[self.cursor_position:]
        self.echo(text)

    def echo(self, text: str) -> None:
        """Speak the provided text.

        :param text: The text to speak, using ``tts.speak``.
        """
        if text == ' ':
            text = 'space'
        self.game.output(text)

    def echo_current_character(self) -> None:
        """Echo the current character.

        Used when moving through the text.
        """
        if self.cursor_position is None:
            return self.echo('')
        self.echo(self.text[self.cursor_position])

    def set_cursor_position(self, pos: Optional[int]) -> None:
        """Set the cursor position within :attr:`~earwax.Editor.text`.

        If ``pos`` is ``None``, then the cursor will be at the end of the line.
        Otherwise, ``pos`` should be an integer between 0 and ``len(self.text)
        - 1``.

        :param pos: The new cursor position.
        """
        if pos is not None and pos >= len(self.text):
            pos = None
        self.cursor_position = pos
        if pos is None:
            return self.echo('')
        self.echo_current_character()

    def clear(self) -> None:
        """Clear this editor.

        By default, this method is called when control + u is pressed.
        """
        self.text = ''
        self.set_cursor_position(None)

    def motion_backspace(self) -> None:
        """Delete the previous character.

        This will do nothing if the cursor is at the beginning of the line, or
        there is no text to delete.
        """
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
        """Delete the character under the cursor.

        Nothing will happen if we are at the end of the line (or there is no
        text, which will amount to the same thing).
        """
        if self.cursor_position is None:
            return self.echo('')
        self.text = self.text[:self.cursor_position] + self.text[
            self.cursor_position + 1:
        ]
        self.echo_current_character()

    def motion_left(self) -> None:
        """Move left in the editor.

        By default, this method is called when the left arrow key is
        pressed.
        """
        if self.cursor_position is None:
            if self.text == '':
                return self.echo('')
            self.set_cursor_position(len(self.text) - 1)
        else:
            self.set_cursor_position(max(0, self.cursor_position - 1))

    def motion_right(self) -> None:
        """Move right in the editor.

        By default, this method is called when the right arrow key is
        pressed.
        """
        if self.cursor_position is None:
            return self.echo('')
        self.set_cursor_position(self.cursor_position + 1)

    def beginning_of_line(self) -> None:
        """Move to the start of the current line.

        By default, this method is called when the home key is pressed.
        """
        self.set_cursor_position(0)

    def end_of_line(self) -> None:
        """Move to the end of the line.

        By default, this method is called when the end key is pressed.
        """
        self.set_cursor_position(None)

    def motion_up(self) -> None:
        """Since we're not bothering with multiline text fields at this stage,
        just move the cursor to the start of the line, and read the whole
        thing.

        By default, this method is called when the up arrow key is pressed.
        """
        self.cursor_position = 0
        self.echo(self.text)

    def motion_down(self) -> None:
        """Since we're not bothering with multiline text fields at this stage,
        just move the cursor to the end of the line, and read the whole
        thing.

        By default, this method is called when the down arrow key ispressed.
        """
        self.cursor_position = None
        self.echo(self.text)
