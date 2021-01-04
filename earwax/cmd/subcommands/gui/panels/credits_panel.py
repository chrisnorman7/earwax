"""Provides the CreditsPanel class."""

import webbrowser
from typing import TYPE_CHECKING, Optional

try:
    import wx
    from synthizer import DirectSource, StreamingGenerator, SynthizerError
    from wx.lib.filebrowsebutton import FileBrowseButton
    from wx.lib.sized_controls import SizedPanel
except ModuleNotFoundError:
    DirectSource, StreamingGenerator, SynthizerError = (None, None, None)
    FileBrowseButton, SizedPanel = (object, object)
    from .. import pretend_wx as wx

from earwax.cmd.constants import sounds_directory
from earwax.cmd.project import Project
from earwax.cmd.project_credit import ProjectCredit

from ..utils import show_error

if TYPE_CHECKING:
    from ..main_frame import MainFrame


class CreditsPanel(wx.Panel):
    """A panel for viewing and editing project credits."""

    def __init__(self, parent: 'MainFrame') -> None:
        """Initialise the panel."""
        self.parent: 'MainFrame' = parent
        self.generator: Optional[StreamingGenerator] = None
        self.source: DirectSource = DirectSource(parent.context)
        super().__init__(parent.notebook)
        self.project: Project = parent.project
        s: wx.BoxSizer = wx.BoxSizer(wx.VERTICAL)
        s.Add(wx.StaticText(self, label='&Credits'), 0, wx.GROW)
        self.credits: wx.ListCtrl = wx.ListCtrl(self, style=wx.LC_REPORT)
        name: str
        for name in ('Name', 'Url', 'Sound Path', 'Loop'):
            self.credits.AppendColumn(name)
        self.credits.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.on_focus_change)
        s.Add(self.credits, 1, wx.GROW)
        p: SizedPanel = SizedPanel(self)
        p.SetSizerType('form')
        self.add_button: wx.Button = wx.Button(p, label='&Add')
        self.add_button.Bind(wx.EVT_BUTTON, self.do_add)
        self.delete_button: wx.Button = wx.Button(p, label='&Delete')
        self.delete_button.Bind(wx.EVT_BUTTON, self.do_delete)
        wx.StaticText(p, label='&Name')
        self.name_ctrl: wx.TextCtrl = wx.TextCtrl(p)
        wx.StaticText(p, label='&Url')
        self.url_ctrl: wx.TextCtrl = wx.TextCtrl(p)
        self.sound_ctrl: FileBrowseButton = FileBrowseButton(
            p, labelText='&Sound', dialogTitle='Choose a sound file',
            startDirectory=str(sounds_directory)
        )
        self.loop_ctrl: wx.CheckBox = wx.CheckBox(p, label='&Loop Sound')
        self.loop_ctrl.Disable()
        self.test_sound: wx.Button = wx.Button(p, label='Test S&ound')
        self.test_sound.Bind(wx.EVT_BUTTON, self.do_test_sound)
        self.test_url: wx.Button = wx.Button(p, label='&Test URL')
        self.test_url.Bind(wx.EVT_BUTTON, self.do_test_url)
        self.update_button: wx.Button = wx.Button(p, label='U&pdate')
        self.update_button.Bind(wx.EVT_BUTTON, self.do_update)
        self.reset_button: wx.Button = wx.Button(p, label='&Reset')
        self.reset_button.Bind(wx.EVT_BUTTON, self.do_reset)
        s.Add(p, 1, wx.GROW)
        self.SetSizerAndFit(s)
        self.load_credits(0)

    def load_credits(self, index: int) -> None:
        """Load all credits, and set selection."""
        self.credits.DeleteAllItems()
        credit: ProjectCredit
        for credit in self.project.credits:
            self.credits.Append(
                (
                    credit.name,
                    credit.url,
                    credit.sound,
                    '*' if credit.loop else 'x'
                )
            )
        self.credits.Focus(index)
        self.credits.EnsureVisible(index)
        self.credits.Select(index)
        self.on_focus_change(wx.ListEvent())

    def get_current_item(self) -> Optional[ProjectCredit]:
        """Return the currently-selected credit."""
        index: int = self.credits.GetFocusedItem()
        if index == -1:
            return None
        return self.project.credits[index]

    def do_add(self, event: wx.CommandEvent) -> None:
        """Add a new credit."""
        self.project.credits.append(
            ProjectCredit('Nameless', 'example.com', None, True)
        )
        self.load_credits(len(self.project.credits) - 1)

    def do_delete(self, event: wx.CommandEvent) -> None:
        """Delete the currently selected credit."""
        credit: Optional[ProjectCredit] = self.get_current_item()
        if credit is None:
            return wx.Bell()
        if wx.MessageBox(
            f'Are you sure you want to delete the {credit.name} credit?',
            caption='Warning', style=wx.ICON_EXCLAMATION | wx.YES_NO
        ) == wx.YES:
            self.project.credits.remove(credit)
            self.load_credits(self.credits.GetFocusedItem() - 1)

    def on_focus_change(self, event: wx.ListEvent) -> None:
        """Handle the currently-focussed credit changing."""
        credit: Optional[ProjectCredit] = self.get_current_item()
        if credit is None:
            self.name_ctrl.Clear()
            self.url_ctrl.Clear()
            self.loop_ctrl.Disable()
            self.sound_ctrl.SetValue('')
            if self.generator is not None:
                self.generator.destroy()
                self.generator = None
        else:
            self.reset_credit(credit)
            self.maybe_play(credit.sound)

    def reset_credit(self, credit: ProjectCredit) -> None:
        """Reset a credit to its defaults.

        :param credit: The credit to reset.
        """
        self.name_ctrl.SetValue(credit.name)
        self.url_ctrl.SetValue(credit.url)
        self.sound_ctrl.SetValue(credit.sound or '')
        self.loop_ctrl.Enable()
        self.loop_ctrl.SetValue(credit.loop)

    def do_update(self, event: wx.CommandEvent) -> None:
        """Update the currently-focussed credit."""
        credit: Optional[ProjectCredit] = self.get_current_item()
        if credit is None:
            return wx.Bell()
        name: str = self.name_ctrl.GetValue()
        if not name:
            show_error('You must enter a name.')
            return self.name_ctrl.SetFocus()
        credit.name = name
        url: str = self.url_ctrl.GetValue()
        if not url:
            show_error('You must enter a URL.')
            return self.url_ctrl.SetFocus()
        credit.url = url
        credit.sound = self.sound_ctrl.GetValue()
        if not credit.sound:
            credit.sound = None
        credit.loop = self.loop_ctrl.GetValue()
        self.load_credits(self.credits.GetFocusedItem())

    def do_reset(self, event: wx.CommandEvent) -> None:
        """Reset the currently-focussed credit."""
        credit: Optional[ProjectCredit] = self.get_current_item()
        if credit is None:
            return wx.Bell()
        self.reset_credit(credit)

    def do_test_sound(self, event: wx.CommandEvent) -> None:
        """Play the sound for the currently-focussed credit."""
        sound: str = self.sound_ctrl.GetValue()
        credit: Optional[ProjectCredit] = self.get_current_item()
        if credit is None:
            return wx.Bell()
        elif credit.sound is None and not sound:
            show_error('This credit has no sound to play')
            self.sound_ctrl.SetFocus()
        else:
            try:
                self.maybe_play(credit.sound or sound)
            except SynthizerError as e:
                show_error(str(e))
                self.sound_ctrl.SetFocus()

    def do_test_url(self, event: wx.CommandEvent) -> None:
        """Open the current URL in the web browser."""
        url: str = self.url_ctrl.GetValue()
        if url:
            webbrowser.open(url)
        else:
            wx.Bell()

    def maybe_play(self, sound: Optional[str]) -> None:
        """Play the given sound, if it is not ``None``.

        :param sound: The path to a sound to play.
        """
        if self.generator is not None:
            self.generator.destroy()
        if sound is not None:
            self.generator = StreamingGenerator(
                self.parent.context, 'file', sound
            )
            self.source.add_generator(self.generator)
        else:
            self.generator = None
