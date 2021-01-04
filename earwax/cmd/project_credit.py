"""Provides the ProjectCredit class."""

from pathlib import Path
from typing import Optional

from attr import attrs

from earwax.mixins import DumpLoadMixin


@attrs(auto_attribs=True)
class ProjectCredit(DumpLoadMixin):
    """A representation of the :class:`earwax.Credit` class.

    This class has a different name to avoid possible confusion.

    :ivar name: The name of what is being credited.

    :ivar url: A URL for this credit.

    :ivar sound: The sound that will play when this credit is shown in a menu.

    :ivar loop: Whether or not :attr:`ProjectCredit.sound` should loop.
    """

    name: str
    url: str
    sound: Optional[str]
    loop: bool

    @property
    def path(self) -> Optional[Path]:
        """Return :attr:`ProjectCredit.sound` as a path."""
        if self.sound is None:
            return None
        return Path(self.sound)
