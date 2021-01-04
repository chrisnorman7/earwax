"""Provides various events for the functioning of the API."""

try:
    from wx.lib.newevent import NewEvent
    SaveEvent, EVT_SAVE = NewEvent()
    VariableEditDoneEvent, EVT_VARIABLE_EDIT_DONE = NewEvent()
except ModuleNotFoundError:
    SaveEvent, EVT_SAVE = (None, None)
    VariableEditDoneEvent, EVT_VARIABLE_EDIT_DONE = (None, None)
