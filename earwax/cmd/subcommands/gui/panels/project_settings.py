"""Provides the ProjectSettings class."""

from typing import TYPE_CHECKING

import wx
from wx.lib.sized_controls import SizedPanel

from earwax.cmd.project import Project

from ..events import EVT_SAVE, SaveEvent

if TYPE_CHECKING:
    from ..main_frame import MainFrame


class ProjectSettings(SizedPanel):
    """Project settings."""

    def __init__(self, parent: 'MainFrame') -> None:
        """Create the panel."""
        self.parent: 'MainFrame' = parent
        super().__init__(parent.notebook)
        self.SetSizerType('form')
        self.parent.Bind(EVT_SAVE, self.on_save)
        self.project: Project = parent.project
        wx.StaticText(self, label='&Name')
        self.name_ctrl = wx.TextCtrl(self, name='', value=parent.project.title)
        self.name_ctrl.Bind(wx.EVT_KEY_UP, self.on_text)
        wx.StaticText(self, label='&Author')
        self.author_ctrl = wx.TextCtrl(self, value=self.project.author)
        wx.StaticText(self, label='&Description')
        self.description_ctrl = wx.TextCtrl(
            self, style=wx.TE_MULTILINE, value=self.project.description
        )
        wx.StaticText(self, label='&Version')
        self.version_ctrl = wx.TextCtrl(self, value=self.project.version)

    def on_save(self, event: SaveEvent) -> None:
        """Update the project with values from this panel."""
        self.project.author = self.author_ctrl.GetValue()
        self.project.description = self.description_ctrl.GetValue()
        self.project.version = self.version_ctrl.GetValue()
        event.Skip()

    def on_text(self, event: wx.KeyEvent) -> None:
        """Handle characters being typed."""
        event.Skip()
        self.project.title = self.name_ctrl.GetValue()
        self.parent.set_title()
