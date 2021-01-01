"""Provides the ProjectSettings class."""

from typing import TYPE_CHECKING

import wx
from wx.lib.sized_controls import SizedPanel

from earwax.cmd.project import Project

if TYPE_CHECKING:
    from ..main_frame import MainFrame


class ProjectSettings(SizedPanel):
    """Project settings."""

    parent: 'MainFrame'
    project: Project

    def __init__(self, parent: 'MainFrame') -> None:
        """Create the panel."""
        self.parent = parent
        super().__init__(parent.notebook)
        self.project = parent.project
        wx.StaticText(self, label='Project &Name')
        self.name_ctrl = wx.TextCtrl(self, name='', value=parent.project.title)
        self.name_ctrl.Bind(wx.EVT_KEY_UP, self.on_text)

    def on_text(self, event: wx.KeyEvent) -> None:
        """Handle characters being typed."""
        event.Skip()
        self.project.title = self.name_ctrl.GetValue()
        self.parent.set_title()
