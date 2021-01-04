"""Provides the LevelsPanel class."""

from typing import TYPE_CHECKING, Dict, Type

try:
    import wx
except ModuleNotFoundError:
    from .. import pretend_wx as wx

from earwax.cmd.game_level import BoxLevelData, GameLevel, LevelData
from earwax.cmd.project import Project

if TYPE_CHECKING:
    from ..main_frame import MainFrame


data_names: Dict[Type, str] = {
    LevelData: 'Standard Level',
    BoxLevelData: 'Map'
}


class LevelsPanel(wx.Panel):
    """A panel to display project levels."""

    def __init__(self, parent: 'MainFrame') -> None:
        """Create the panel."""
        self.parent: 'MainFrame' = parent
        super().__init__(parent.notebook)
        self.project: Project = parent.project
        s: wx.BoxSizer = wx.BoxSizer(wx.VERTICAL)
        s.Add(wx.StaticText(self, label='&Levels'), 0, wx.GROW)
        self.levels: wx.ListCtrl = wx.ListCtrl(self, style=wx.LC_REPORT)
        name: str
        for name in ('Name', 'Type'):
            self.levels.AppendColumn(name)
        self.load_levels(0)
        s.Add(self.levels, 1, wx.GROW)
        s2: wx.BoxSizer = wx.BoxSizer()
        self.add_button: wx.Button = wx.Button(self, label='&Add')
        s2.Add(self.add_button, 0, wx.GROW)
        self.remove_button: wx.Button = wx.Button(self, label='&Remove')
        s2.Add(self.remove_button, 0, wx.GROW)
        s.Add(s2, 0, wx.GROW)
        self.SetSizerAndFit(s)

    def load_levels(self, index: int) -> None:
        """Reload the game levels and set selection.

        :param index: The item to focus after loading.
        """
        self.levels.DeleteAllItems()
        level: GameLevel
        for level in self.project.levels:
            self.levels.Append(
                (
                    level.name,
                    data_names[type(level.data)]
                )
            )
        self.levels.Focus(index)
        self.levels.EnsureVisible(index)
        self.levels.Select(index)
