"""Provides the MainFrame class."""

import wx

from earwax.cmd.project import Project

from .panels.project_settings import ProjectSettings


class MainFrame(wx.Frame):
    """The main frame of the earwax gui client."""

    project: Project
    notebook: wx.Notebook

    def __init__(self) -> None:
        """Initialise the window."""
        super().__init__(None, title='Earwax')
        self.project = Project.load()
        self.set_title()
        p: wx.Panel = wx.Panel(self)
        s: wx.BoxSizer = wx.BoxSizer(orient=wx.VERTICAL)
        self.notebook = wx.Notebook(p, name='')
        self.notebook.AddPage(
            ProjectSettings(self), 'Project &Settings'
        )
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
        self.project.save()
