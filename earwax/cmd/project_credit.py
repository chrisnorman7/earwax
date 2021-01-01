"""Provides the ProjectCredit class."""

from pathlib import Path
from typing import Any, Dict, Optional, Union, cast

from attr import asdict, attrs

ProjectCreditDict = Dict[str, Optional[Union[str, bool]]]


@attrs(auto_attribs=True)
class ProjectCredit:
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

    def dump(self) -> ProjectCreditDict:
        """Return this object as a dictionary."""
        return asdict(self)

    @classmethod
    def load(cls, data: ProjectCreditDict) -> 'ProjectCredit':
        """Load and return an instance from the given data.

        :param data: The data to load.
        """
        return cls(**cast(Dict[str, Any], data))
