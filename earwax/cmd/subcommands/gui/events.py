"""Provides various events for the functioning of the API."""

from wx.lib.newevent import NewEvent

SaveEvent, EVT_SAVE = NewEvent()
VariableEditDoneEvent, EVT_VARIABLE_EDIT_DONE = NewEvent()
