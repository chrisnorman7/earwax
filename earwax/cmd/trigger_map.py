"""Provides the Trigger and TriggerMap classes."""

from typing import List, Optional

from attr import Factory, attrs
from shortuuid import uuid

from ..mixins import DumpLoadMixin


@attrs(auto_attribs=True)
class Trigger(DumpLoadMixin):
    """A trigger that can activate a function in a game."""

    symbol: Optional[str] = None
    modifiers: List[str] = Factory(list)
    mouse_button: Optional[str] = None
    hat_directions: Optional[str] = None
    joystick_button: Optional[int] = None
    id: str = Factory(uuid)
