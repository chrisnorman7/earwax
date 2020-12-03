"""Provides the Editor class."""

from typing import Optional

from attr import attrs

from .hat_directions import DOWN, LEFT, RIGHT, UP

try:
    from pyglet.window import key
except ModuleNotFoundError:
    key = None

from .level import Level
from .mixins import DismissibleMixin


@attrs(auto_attribs=True)
class Editor(Level, DismissibleMixin):
    """A basic text editor.

    By default, the enter key dispatches the ``on_submit`` event, with the
    contents of :attr:`earwax.Editor.text`.

    Below is an example of how to use this class::

        e: Editor = Editor(game)

        @e.event
        def on_submit(text: str) -> None:
            # Do something with text...

        game.push_level(e)

    :ivar ~earwax.editor.EditorBase.func: The function which should be called
        when pressing enter in an edit field.

    :ivar ~earwax.Editor.text: The text which can be edited by this object.

    :ivar ~earwax.Editor.cursor_position: The position of the cursor.

    :ivar ~earwax.Editor.vertical_position: The position in the alphabet of the
        hat.
    """

    text: str = ''
    cursor_position: Optional[int] = None
    vertical_position: Optional[int] = None

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
        self.action('Choose previous letter', hat_direction=UP)(self.hat_up)
        self.motion(key.MOTION_DOWN)(self.motion_down)
        self.action('Choose next letter', hat_direction=DOWN)(self.hat_down)
        self.action('Submit text', symbol=key.RETURN)(self.submit)
        self.action('Dismiss', symbol=key.ESCAPE)(self.dismiss)
        self.action('Clear', symbol=key.U, modifiers=key.MOD_CTRL)(self.clear)
        for func in (self.on_text, self.on_submit):
            self.register_event_type(func.__name__)
        return super().__attrs_post_init__()

    def submit(self) -> None:
        """Submit :attr:`self.text <earwax.Editor.text>`.

        Dispatch the :attr:`~earwax.Editor.on_submit` event with the contents
        of :attr:`self.text <earwax.Editor.text>`.

        By default, this method is called when the enter key is pressed.
        """
        self.dispatch_event('on_submit', self.text)

    def insert_text(self, text: str) -> None:
        """Insert ``text`` at the current cursor position."""
        self.text = self.text[:self.cursor_position] + text + self.text[
            self.cursor_position:
        ]

    def on_text(self, text: str) -> None:
        """Text has been entered.

        If the cursor is at the end of the line, append the text. Otherwise,
        insert it.

        :param text: The text that has been entered.
        """
        if self.cursor_position is None:
            self.text += text
        else:
            self.insert_text(text)
            self.cursor_position += len(text)
        self.echo(text)

    def on_submit(self, text: str) -> None:
        """Code to be run when this editor is submitted.

        The event which is dispatched if the enter key is pressed.

        :param text: The contents of :attr:`self.text <earwax.Editor.text>`.
        """
        pass

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
        index: Optional[int]
        try:
            if self.cursor_position is None:
                index = None
            else:
                index = self.game.config.editors.hat_alphabet.value.index(
                    self.text[self.cursor_position]
                )
        except ValueError:
            index = None
        self.vertical_position = index
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

    def do_delete(self) -> None:
        """Perform a forward delete.

        Used by :meth:`~earwax.Editor.motion_delete`, as well as the vertical
        hat movement methods.
        """
        if self.cursor_position is not None:
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
        self.do_delete()
        self.set_cursor_position(self.cursor_position)

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
        """Arrow up.

        Since we're not bothering with multiline text fields at this stage,
        just move the cursor to the start of the line, and read the whole
        thing.

        By default, this method is called when the up arrow key is pressed.
        """
        self.cursor_position = 0
        self.echo(self.text)

    def motion_down(self) -> None:
        """Arrow down.

        Since we're not bothering with multiline text fields at this stage,
        just move the cursor to the end of the line, and read the whole
        thing.

        By default, this method is called when the down arrow key is pressed.
        """
        self.cursor_position = None
        self.echo(self.text)

    def hat_up(self) -> None:
        """Change the current letter to the previous one in the configured alphabet.

        If the cursor is at the end of the line, moving up will select a "save"
        button.

        If the cursor is not at the end of the line, moving up will select a
        "delete" button.
        """
        if self.vertical_position == -1:
            if self.cursor_position is None:
                self.submit()
            else:
                self.motion_delete()
        else:
            if self.vertical_position is None:
                self.vertical_position = 0
            self.vertical_position -= 1
            if self.vertical_position == -1:
                if self.cursor_position is None:
                    self.echo('Submit')
                else:
                    self.echo('Delete')
            else:
                self.do_delete()
                self.on_text(
                    self.game.config.editors.hat_alphabet.value[
                        self.vertical_position
                    ]
                )
                if self.cursor_position is not None:
                    self.cursor_position -= 1

    def hat_down(self) -> None:
        """Move down through the list of letters."""
        letters: str = self.game.config.editors.hat_alphabet.value
        if self.vertical_position is None:
            self.vertical_position = -1
        self.vertical_position = (self.vertical_position + 1) % len(letters)
        letter: str = letters[self.vertical_position]
        # The next line won't work if the cursor is at the end, so no need to
        # check.
        self.do_delete()
        self.on_text(letter)
        if self.cursor_position is None:
            self.cursor_position = (len(self.text) - 1)
        else:
            self.cursor_position -= 1
