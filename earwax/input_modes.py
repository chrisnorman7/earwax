"""Provides the InputModes enumeration."""

from enum import Enum


class InputModes(Enum):
    """The possible input modes.

    This enumeration is used to show appropriate triggers in
    :class:`earwax.ActionMenu` instances.

    :ivar ~earwax.InputModes.keyboard: The user is entering commands via
        keyboard or mouse.

    :ivar ~earwax.InputModes.controller: The user is using a games controller.
    """

    keyboard = 0
    controller = 1
