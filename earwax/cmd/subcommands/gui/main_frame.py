"""Provides the MainFrame class."""

import wx

from earwax.cmd.project import Project

from .events import EVT_SAVE, SaveEvent
from .panels.project_settings import ProjectSettings
from .panels.variables_panel import VariablesPanel


class MainFrame(wx.Frame):
    """The main frame of the earwax gui client."""

    def __init__(self) -> None:
        """Initialise the window."""
        super().__init__(None, title='Earwax')
        self.project: Project = Project.load()
        self.set_title()
        self.Bind(EVT_SAVE, self.on_save)
        p: wx.Panel = wx.Panel(self)
        s: wx.BoxSizer = wx.BoxSizer(orient=wx.VERTICAL)
        self.notebook: wx.Notebook = wx.Notebook(p, name='')
        self.project_settings: ProjectSettings = ProjectSettings(self)
        self.variables_panel: VariablesPanel = VariablesPanel(self)
        self.notebook.AddPage(self.project_settings, 'Project &Settings')
        self.notebook.AddPage(self.variables_panel, '&Variables')
        s.Add(self.notebook, 1, wx.GROW)
        s2: wx.BoxSizer = wx.BoxSizer()
        self.save_button = wx.Button(p, name='', label='&Save')
        s2.Add(self.save_button, 1, wx.GROW)
        self.save_button.Bind(wx.EVT_BUTTON, self.do_save)
        s.Add(s2, 0, wx.GROW)
        p.SetSizerAndFit(s)

    def set_title(self) -> None:
        """Set the window title."""
        self.SetTitle(f'Earwax - {self.project.title}')

    def do_save(self, event: wx.CommandEvent) -> None:
        """Performa  save."""
        event = SaveEvent(project=self.project)
        wx.PostEvent(self, event)

    def on_save(self, event: SaveEvent) -> None:
        """Perform the save."""
        self.project.save()
        event.Skip()
