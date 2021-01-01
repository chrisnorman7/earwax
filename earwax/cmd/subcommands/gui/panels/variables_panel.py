"""Provides the VariablesPanel class."""

from json import dumps
from typing import TYPE_CHECKING, Dict

import wx

from earwax.cmd.variable import Variable, VariableTypes

if TYPE_CHECKING:
    from ..main_frame import MainFrame

from earwax.cmd.project import Project

type_strings: Dict[VariableTypes, str] = {
    VariableTypes.type_bool: 'Boolean',
    VariableTypes.type_string: 'String',
    VariableTypes.type_int: 'Integer',
    VariableTypes.type_float: 'Float'
}


class VariablesPanel(wx.Panel):
    """A panel for displaying variables."""

    def __init__(self, parent: 'MainFrame') -> None:
        """Create the panel."""
        self.parent: 'MainFrame' = parent
        super().__init__(parent.notebook)
        self.project: Project = parent.project
        s: wx.BoxSizer = wx.BoxSizer(wx.VERTICAL)
        s.Add(wx.StaticText(self, label='&Variables'), 0, wx.GROW)
        self.variables: wx.ListCtrl = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.variables.AppendColumn('Name')
        self.variables.AppendColumn('Value')
        self.variables.AppendColumn('Type')
        variable: Variable
        for variable in self.project.variables:
            self.variables.Append(
                (
                    variable.name,
                    dumps(variable.value),
                    type_strings[variable.get_type()]
                )
            )
        s.Add(self.variables, 1, wx.GROW)
        s2: wx.BoxSizer = wx.BoxSizer()
        self.add_button = wx.Button(self, label='&Add')
        self.edit_button = wx.Button(self, label='&Edit')
        self.delete_button = wx.Button(self, label='&Delete')
        s2.AddMany(
            (
                (self.add_button, 0, wx.GROW),
                (self.edit_button, 0, wx.GROW),
                (self.delete_button, 0, wx.GROW)
            )
        )
        s.Add(s2, 0, wx.GROW)
        self.SetSizerAndFit(s)