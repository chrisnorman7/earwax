"""Provides the gui sub command."""

from argparse import Namespace

try:
    import wx
    from synthizer import initialized
except ModuleNotFoundError:
    from . import pretend_wx as wx
    initialized = None

from earwax.cmd.constants import project_filename


def gui(args: Namespace) -> None:
    """Open a GUI to configure your project."""
    if wx is None:
        print('You do not appear to have wx installed.')
        print()
        print('Try typing `pip install -U wxpython`.')
    elif not project_filename.is_file():
        print('No earwax project file found.')
        print()
        print('Try typing `earwax init` first.')
    else:
        from .main_frame import MainFrame
        a: wx.App = wx.App(False)
        with initialized():
            f: MainFrame = MainFrame()
            f.Show()
            f.Maximize(True)
            f.Layout()
            a.MainLoop()
