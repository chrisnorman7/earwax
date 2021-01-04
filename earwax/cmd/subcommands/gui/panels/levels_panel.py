"""Provides the LevelsPanel class."""

from typing import TYPE_CHECKING, Dict, List, Optional, Type

try:
    import wx
except ModuleNotFoundError:
    from .. import pretend_wx as wx

from earwax.cmd.game_level import BoxLevelData, GameLevel, LevelData
from earwax.cmd.project import Project

from ..events import EVT_LEVEL_EDIT_DONE
from .edit_level_frame import EditLevelFrame

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
        self.levels.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.do_edit)
        self.load_levels(0)
        s.Add(self.levels, 1, wx.GROW)
        s2: wx.BoxSizer = wx.BoxSizer()
        self.add_button: wx.Button = wx.Button(self, label='&Add')
        self.add_button.Bind(wx.EVT_BUTTON, self.do_add_level)
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

    def get_current_item(self) -> Optional[GameLevel]:
        """Return the currently-selected level."""
        index: int = self.levels.GetFocusedItem()
        if index == -1:
            return None
        return self.project.levels[index]

    def edit_level(self, level: GameLevel) -> None:
        """Edit the provided level.

        :param level: The level to edit.
        """
        f: EditLevelFrame = EditLevelFrame(self, level)
        f.Bind(
            EVT_LEVEL_EDIT_DONE,
            lambda event: self.load_levels(self.levels.GetFocusedItem())
        )
        f.Show(True)
        f.Maximize(True)

    def do_edit(self, event: wx.CommandEvent) -> None:
        """Edit the currently-selected level."""
        level: Optional[GameLevel] = self.get_current_item()
        if level is None:
            return wx.Bell()
        self.edit_level(level)

    def do_add_level(self, even: wx.CommandEvent) -> None:
        """Add a new level to this project."""
        dlg: wx.SingleChoiceDialog
        with wx.SingleChoiceDialog(
            self.parent, 'Choose a type for your new level', 'Level Type',
            list(data_names.values())
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                level_types: List[Type] = list(data_names)
                data_type: Type = level_types[dlg.GetSelection()]
                gl: GameLevel = GameLevel('Untitled Level', data_type())
                self.project.levels.append(gl)
                self.load_levels(self.levels.GetFocusedItem() + 1)
                self.levels.SetFocus()
                self.edit_level(gl)
