"""Various utility functions."""

import wx


def show_error(message: str, caption: str = 'Error') -> int:
    """Show an error box.

    :param message: The message to show.

    :param caption: The caption of the dialogue.
    """
    return wx.MessageBox(message, caption=caption, style=wx.ICON_EXCLAMATION)