"""Provides the EditVariablePanel class."""

from json import dumps, loads
from typing import Any, List

try:
    import wx
    from wx.lib.sized_controls import SizedFrame, SizedPanel
except ModuleNotFoundError:
    SizedPanel, SizedFrame = (object, object)
    from .. import pretend_wx as wx

from earwax.cmd.project import Project
from earwax.cmd.variable import Variable, VariableTypes, type_strings

from ..events import VariableEditDoneEvent
from ..utils import show_error


class EditVariableFrame(SizedFrame):
    """A frame for editing and creating variables."""

    def __init__(self, project: Project, variable: Variable) -> None:
        """Initialise the frame."""
        self.variable = variable
        self.project = project
        super().__init__(
            None,
            title=f'{"Edit" if variable in project.variables else "Add New"} '
            'Variable'
        )
        p: SizedPanel = self.GetContentsPane()
        p.SetSizerType('form')
        wx.StaticText(p, label='&Name')
        self.name_ctrl = wx.TextCtrl(p, value=variable.name)
        wx.StaticText(p, label='&Type')
        self.type_ctrl = wx.Choice(p, choices=list(type_strings.values()))
        self.type_ctrl.SetStringSelection(type_strings[variable.get_type()])
        wx.StaticText(p, label='&Value')
        self.value_ctrl = wx.TextCtrl(
            p,
            value=variable.value
            if variable.get_type() is VariableTypes.type_string else
            dumps(variable.value)
        )
        self.ok_button = wx.Button(p, label='&OK')
        self.ok_button.SetDefault()
        self.cancel_button = wx.Button(p, label='&Cancel')
        self.ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

    def on_ok(self, event: wx.CommandEvent) -> None:
        """Store the new value."""
        types: List[VariableTypes] = list(type_strings.keys())
        new_type: VariableTypes = types[self.type_ctrl.GetSelection()]
        value: Any = self.value_ctrl.GetValue()
        if new_type is not VariableTypes.type_string:
            if new_type is VariableTypes.type_float and '.' not in value:
                value += '.0'
            try:
                value = loads(value)
            except ValueError as e:
                show_error(str(e))
                return None
        new: Variable = Variable('Temporary', new_type, value)
        actual_type: VariableTypes
        try:
            actual_type = new.get_type()
        except TypeError:
            show_error('Invalid value.')
            return None
        if new_type is not actual_type:
            show_error(
                'The type of the value you entered is different to the type '
                'you selected.',
                caption='Type Mismatch'
            )
            return None
        self.variable.name = self.name_ctrl.GetValue()
        self.variable.type = new_type
        self.variable.value = value
        if self.variable not in self.project.variables:
            self.project.variables.append(self.variable)
        evt: VariableEditDoneEvent = VariableEditDoneEvent(
            project=self.project, variable=self.variable
        )
        wx.PostEvent(self, evt)
        self.Close(True)

    def on_cancel(self, event: wx.CommandEvent) -> None:
        """Close the window."""
        self.Close(True)
