"""Provides function for working with sdl2."""

import sys

from sdl2 import SDL_GetError


class SdlError(Exception):
    """An error in SDL."""


def sdl_raise() -> None:
    """Raise the most recent SDL error."""
    e: bytes = SDL_GetError()
    e_string: str = e.decode(sys.getdefaultencoding(), errors='replace')
    if e:
        raise SdlError(e_string)


def maybe_raise(value: int) -> None:
    """Possibly raise :class:`~earwax.SdlError`.

    :param value: The value of an sdl function.

        If this value is ``-1``, then an error will be raised.
    """
    if value == -1:
        sdl_raise()
