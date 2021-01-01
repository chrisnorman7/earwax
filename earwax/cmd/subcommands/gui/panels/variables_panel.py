"""Provides the VariablesPanel class."""

from json import dumps
from typing import TYPE_CHECKING, Optional

import wx

from ..events import EVT_VARIABLE_EDIT_DONE, VariableEditDoneEvent
from .edit_variable_frame import EditVariableFrame

if TYPE_CHECKING:
    from ..main_frame import MainFrame

from earwax.cmd.project import Project
from earwax.cmd.variable import Variable, VariableTypes, type_strings


class VariablesPanel(wx.Panel):
    """A panel for displaying variables."""

    def __init__(self, parent: 'MainFrame') -> None:
        """Create the panel."""
        self.edit_variable_frame: Optional[EditVariableFrame] = None
        self.parent: 'MainFrame' = parent
        super().__init__(parent.notebook)
        parent.Bind(wx.EVT_CLOSE, self.on_parent_close)
        self.project: Project = parent.project
        s: wx.BoxSizer = wx.BoxSizer(wx.VERTICAL)
        s.Add(wx.StaticText(self, label='&Variables'), 0, wx.GROW)
        self.variables: wx.ListCtrl = wx.ListCtrl(self, style=wx.LC_REPORT)
        name: str
        for name in ('Name', 'Value', 'Type'):
            self.variables.AppendColumn(name)
        self.variables.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.do_edit)
        s.Add(self.variables, 1, wx.GROW)
        s2: wx.BoxSizer = wx.BoxSizer()
        self.add_button = wx.Button(self, label='&Add')
        self.add_button.Bind(wx.EVT_BUTTON, self.do_add)
        self.edit_button = wx.Button(self, label='&Edit')
        self.edit_button.Bind(wx.EVT_BUTTON, self.do_edit)
        self.delete_button = wx.Button(self, label='&Delete')
        self.delete_button.Bind(wx.EVT_BUTTON, self.do_delete)
        s2.AddMany(
            (
                (self.add_button, 0, wx.GROW),
                (self.edit_button, 0, wx.GROW),
                (self.delete_button, 0, wx.GROW)
            )
        )
        s.Add(s2, 0, wx.GROW)
        self.SetSizerAndFit(s)
        self.load_variables(0)

    def load_variables(self, index: int) -> None:
        """Load all variables, and set selection."""
        self.variables.DeleteAllItems()
        variable: Variable
        for variable in self.project.variables:
            self.variables.Append(
                (
                    variable.name,
                    variable.value
                    if variable.get_type() is VariableTypes.type_string else
                    dumps(variable.value),
                    type_strings[variable.get_type()]
                )
            )
        self.variables.Focus(index)
        self.variables.EnsureVisible(index)
        self.variables.Select(index)

    def get_current_item(self) -> Optional[Variable]:
        """Return the currently-selected variable."""
        index: int = self.variables.GetFirstSelected()
        if index == -1:
            return None
        return self.project.variables[index]

    def set_controls(self, enabled: bool) -> None:
        """Enable or disable all controls."""
        for control in (
            self.variables, self.add_button, self.edit_button,
            self.delete_button
        ):
            if enabled:
                control.Enable()
            else:
                control.Disable()

    def do_add(self, event: wx.CommandEvent) -> None:
        """Add a new variable."""
        self.edit_variable(Variable('Untitled variable', ''))

    def do_edit(self, event: wx.CommandEvent) -> None:
        """Edit the selected variable."""
        variable: Optional[Variable] = self.get_current_item()
        if variable is None:
            return wx.Bell()
        self.edit_variable(variable)

    def edit_variable(self, variable: Variable) -> None:
        """Edit the given variable in a new window.

        :param variable: The variable to edit.

            This could be a new variable, in which case it will be added to the
            variables list when editing is finished.
        """
        self.set_controls(False)
        self.edit_variable_frame = EditVariableFrame(self.project, variable)
        self.edit_variable_frame.Bind(
            EVT_VARIABLE_EDIT_DONE, self.on_finish_edit
        )
        self.edit_variable_frame.Bind(wx.EVT_CLOSE, self.enable_controls)
        self.edit_variable_frame.ShowFullScreen(True)
        self.edit_variable_frame.Maximize(True)

    def on_finish_edit(self, event: VariableEditDoneEvent) -> None:
        """Reload variables."""
        self.load_variables(self.variables.GetFirstSelected())
        self.variables.SetFocus()

    def enable_controls(self, event: wx.CloseEvent) -> None:
        """Re-enable controls."""
        self.set_controls(True)
        self.edit_variable_frame = None
        event.Skip()

    def do_delete(self, event: wx.CommandEvent) -> None:
        """Delete the currently selected variable."""
        variable: Optional[Variable] = self.get_current_item()
        if variable is None:
            return wx.Bell()
        if wx.MessageBox(
            f'Are you sure you want to delete the {variable.name} variable?',
            caption='Warning', style=wx.ICON_EXCLAMATION | wx.YES_NO
        ) == wx.YES:
            self.project.variables.remove(variable)
            self.load_variables(self.variables.GetFirstSelected() - 1)

    def on_parent_close(self, event: wx.CloseEvent) -> None:
        """Close any edit frame that is currently open."""
        if self.edit_variable_frame is not None:
            self.edit_variable_frame.Close()
        event.Skip()
