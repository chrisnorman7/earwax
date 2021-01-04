"""Provides various events for the functioning of the API."""

from typing import Tuple, Type

try:
    from wx.lib.newevent import NewEvent
except ModuleNotFoundError:

    def NewEvent() -> Tuple[Type, Type]:
        """Return two class values."""
        return (object, object)

SaveEvent, EVT_SAVE = NewEvent()
VariableEditDoneEvent, EVT_VARIABLE_EDIT_DONE = NewEvent()
LevelEditDoneEvent, EVT_LEVEL_EDIT_DONE = NewEvent()
