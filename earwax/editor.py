"""Provides the Editor class."""

from attr import Factory, attrib, attrs
from pyglet.window import key

from .speech import tts


@attrs
class Editor:
    """A basic text editor."""

    # The function to be called with the text in this editor when the enter key
    # is pressed.
    func = attrib()

    # The contents of this editor.
    text = attrib(default=Factory(str))

    # The position of the cursor (None means text should be appended).
    cursor_position = attrib(default=Factory(type(None)))

    # Whether or not it should be possible to dismiss this editor.
    dismissible = attrib(default=Factory(lambda: True))

    # The defined motion events. To define more, use the motion decorator.
    motions = attrib(default=Factory(dict), init=False)

    def __attrs_post_init__(self):
        self.motion(key.MOTION_BACKSPACE)(self.motion_backspace)
        self.motion(key.MOTION_DELETE)(self.motion_delete)
        self.motion(key.MOTION_LEFT)(self.motion_left)
        self.motion(key.MOTION_RIGHT)(self.motion_right)
        self.motion(key.MOTION_BEGINNING_OF_LINE)(self.beginning_of_line)
        self.motion(key.MOTION_END_OF_LINE)(self.end_of_line)
        self.motion(key.MOTION_UP)(self.motion_up)
        self.motion(key.MOTION_DOWN)(self.motion_down)

    def submit(self):
        """Submit the text in this control to self.func."""
        return self.func(self.text)

    def on_text(self, text):
        """Text has been entered.

        If the cursor is at the end of the line, append the text. Otherwise,
        insert it."""
        if self.cursor_position is None:
            self.text += text
        else:
            self.text = self.text[:self.cursor_position] + text +\
                self.text[self.cursor_position:]
        self.echo(text)

    def on_text_motion(self, motion):
        """Handle a motion event."""
        if motion in self.motions:
            return self.motions[motion]()
        raise NotImplementedError(key.motion_string(motion))

    def echo(self, text):
        """Output entered text. Overridden by PasswordEditor, to speak "*"."""
        if text == ' ':
            text = 'space'
        tts.speak(text)

    def echo_current_character(self):
        """Echo the current character."""
        if self.cursor_position is None:
            return self.echo('')
        self.echo(self.text[self.cursor_position])

    def set_cursor_position(self, pos):
        """If pos is None, then the cursor will be at the end of the line.
        Otherwise, pos should be an integer between 0 and len(self.text) -
        1."""
        if pos is not None and pos >= len(self.text):
            pos = None
        self.cursor_position = pos
        if pos is None:
            return self.echo('')
        self.echo_current_character()

    def clear(self):
        """Clear this editor."""
        self.text = ''
        self.set_cursor_position(None)

    def motion(self, motion):
        """A decorator to add a handler to self.motions."""

        def inner(func):
            self.motions[motion] = func
            return func

        return inner

    def motion_backspace(self):
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

    def motion_delete(self):
        """Delete the character under the cursor."""
        if self.cursor_position is None:
            return self.echo('')
        self.text = self.text[:self.cursor_position] + self.text[
            self.cursor_position + 1:
        ]
        self.echo_current_character()

    def motion_left(self):
        """Move left in the editor."""
        if self.cursor_position is None:
            if self.text == '':
                return self.echo('')
            self.set_cursor_position(len(self.text) - 1)
        else:
            self.set_cursor_position(max(0, self.cursor_position - 1))

    def motion_right(self):
        """Move right in the editor."""
        if self.cursor_position is None:
            return self.echo('')
        self.set_cursor_position(self.cursor_position + 1)

    def beginning_of_line(self):
        """Move to the start of the current line."""
        self.set_cursor_position(0)

    def end_of_line(self):
        """Move to the end of the line."""
        self.set_cursor_position(None)

    def motion_up(self):
        """Since we're not bothering with multiline text fields at this stage,
        just move the cursor to the start of the line, and read the whole
        thing."""
        self.cursor_position = 0
        self.echo(self.text)

    def motion_down(self):
        """Since we're not bothering with multiline text fields at this stage,
        just move the cursor to the end of the line, and read the whole
        thing."""
        self.cursor_position = None
        self.echo(self.text)
