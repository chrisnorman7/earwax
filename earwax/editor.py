"""Provides the Editor class."""

from attr import Factory, attrib, attrs

from .speech import tts


@attrs
class Editor:
    """A basic text editor."""

    # The contents of this editor.
    text = attrib(default=Factory(str))

    # The position of the cursor (None means text should be appended).
    cursor_position = attrib(default=Factory(type(None)))

    # Whether or not it should be possible to dismiss this editor.
    dismissible = attrib(default=Factory(lambda: True))

    def on_text(self, text):
        """Text has been entered.

        If cursor_position is None, append the text. Otherwise, insert it."""
        if self.cursor_position is None:
            self.text += text
        else:
            self.text = self.text[:self.cursor_position] + text +\
                self.text[self.cursor_position:]
        self.echo(text)

    def echo(self, text):
        """Output entered text. Overridden by PasswordEditor, to speak "*"."""
        tts.speak(text)
