"""Provides the EditLevelFrame class."""

from typing import Optional

try:
    import wx
    from wx.lib.intctrl import IntCtrl
    from wx.lib.sized_controls import SizedPanel
except ModuleNotFoundError:
    from .. import pretend_wx as wx
    IntCtrl = object
    SizedPanel = object

from typing import TYPE_CHECKING

from earwax.cmd.game_level import (BoxLevelData, GameLevel, GameLevelScript,
                                   LevelData)

from ..events import LevelEditDoneEvent

if TYPE_CHECKING:
    from ..main_frame import MainFrame


class LevelDataPanel(SizedPanel):
    """The parent class for all data panels."""

    def __init__(self, parent: 'EditLevelFrame') -> None:
        """Initialise the panel."""
        self.parent: 'EditLevelFrame' = parent
        super().__init__(parent.notebook)
        self.SetSizerType('form')

    def do_save(self) -> None:
        """Save any values contained by this panel."""
        pass


class GeneralPanel(LevelDataPanel):
    """Allow the configuration of settings common to all level types."""

    def __init__(self, parent: 'EditLevelFrame') -> None:
        """Initialise the panel."""
        super().__init__(parent)
        wx.StaticText(self, label='&Name')
        self.name_ctrl = wx.TextCtrl(self, value=parent.level.name)

    def do_save(self) -> None:
        """Write the name."""
        self.parent.level.name = self.name_ctrl.GetValue()
        return super().do_save()


class ScriptsPanel(wx.Panel):
    """A panel for viewing scripts."""

    def __init__(self, parent: 'EditLevelFrame') -> None:
        """Initialise the panel."""
        self.parent: 'EditLevelFrame' = parent
        super().__init__(parent.notebook)
        s: wx.BoxSizer = wx.BoxSizer(wx.VERTICAL)
        s.Add(wx.StaticText(self, label='&Scripts'), 0, wx.GROW)
        self.scripts: wx.ListCtrl = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.scripts.AppendColumn('Name')
        self.load_scripts(0)
        s.Add(self.scripts, 1, wx.GROW)
        self.SetSizerAndFit(s)

    def load_scripts(self, index: int) -> None:
        """Reload scriptsand set selection.

        :param index: The item to focus after loading.
        """
        self.scripts.DeleteAllItems()
        script: GameLevelScript
        for script in self.parent.level.scripts:
            self.levels.Append((script.name,))
        self.scripts.Focus(index)
        self.scripts.EnsureVisible(index)
        self.scripts.Select(index)

    def get_current_item(self) -> Optional[GameLevelScript]:
        """Return the currently-selected script."""
        index: int = self.scripts.GetFocusedItem()
        if index == -1:
            return None
        return self.parent.level.scripts[index]


class LevelPanel(LevelDataPanel):
    """Basically show an empty panel."""

    def __init__(self, parent: 'EditLevelFrame') -> None:
        """Initialise the panel."""
        super().__init__(parent)
        wx.StaticText(self, label='&Description')
        wx.TextCtrl(
            self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP,
            value='Standard levels have no settings unlike other levels.'
        )


class BoxLevelPanel(LevelDataPanel):
    """A panel to configure box levels."""

    def __init__(self, parent: 'EditLevelFrame') -> None:
        """Initialise the panel."""
        super().__init__(parent)
        wx.StaticText(self, label='Initial &Bearing')
        self.bearing = IntCtrl(self, min=0, max=359, name='')

    def do_save(self) -> None:
        """Save the bearing."""
        assert isinstance(self.parent.level.data, BoxLevelData)
        self.parent.level.data.bearing = self.bearing.GetValue()
        return super().do_save()


class EditLevelFrame(wx.Frame):
    """A frame for editing and creating levels."""

    def __init__(self, parent: 'MainFrame', level: GameLevel) -> None:
        """Initialise the frame."""
        self.level = level
        self.parent: 'MainFrame' = parent
        super().__init__(None, title='Edit Level')
        parent.Bind(wx.EVT_CLOSE, self.on_parent_close)
        p: wx.Panel = wx.Panel(self)
        s: wx.BoxSizer = wx.BoxSizer(wx.VERTICAL)
        self.notebook: wx.Notebook = wx.Notebook(p, name='')
        self.general_panel: GeneralPanel = GeneralPanel(self)
        self.notebook.AddPage(self.general_panel, '&General')
        self.custom_panel: LevelDataPanel
        if isinstance(level.data, LevelData):
            self.custom_panel = LevelPanel(self)
        elif isinstance(level.data, BoxLevelData):
            self.custom_panel = BoxLevelPanel(self)
        else:
            raise RuntimeError('Invalid level data: %r.' % level.data)
        self.notebook.AddPage(self.custom_panel, '&Level')
        self.scripts_panel: ScriptsPanel = ScriptsPanel(self)
        self.notebook.AddPage(self.scripts_panel, '&Scripts')
        s.Add(self.notebook, 1, wx.GROW)
        self.notebook.SetSelection(1)
        s2: wx.BoxSizer = wx.BoxSizer()
        self.ok_button = wx.Button(p, label='&OK')
        self.ok_button.SetDefault()
        self.cancel_button = wx.Button(p, label='&Cancel')
        s2.AddMany(
            (
                (self.ok_button, 0, wx.GROW),
                (self.cancel_button, 0, wx.GROW)
            )
        )
        s.Add(s2, 0, wx.GROW)
        self.ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)
        p.SetSizerAndFit(s)

    def on_ok(self, event: wx.CommandEvent) -> None:
        """Update values and close the window."""
        self.general_panel.do_save()
        self.custom_panel.do_save()
        evt: LevelEditDoneEvent = LevelEditDoneEvent(level=self.level)
        wx.PostEvent(self, evt)
        self.Close(True)

    def on_cancel(self, event: wx.CommandEvent) -> None:
        """Close the window."""
        self.Close(True)

    def on_parent_close(self, event: wx.CloseEvent) -> None:
        """Close this window, because the parent is closing."""
        self.Close(True)
        event.Skip()
