"""Provides the Config class."""

from inspect import isclass
from typing import Any, Dict

from attr import Attribute, asdict, attrs

DumpDict = Dict[str, Any]


@attrs(auto_attribs=True)
class Config:
    """Holds configuration subsections and values."""

    def dump(self) -> DumpDict:
        """Return this object as a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: DumpDict) -> 'Config':
        """Load and return an instance from a dictionary, probably provided by
        :meth:`~earwax.Config.dump`::

            with open('config.json', 'r') as f:
                c = Config.load(**json.load(f))

        As a shortcut, you can use :meth:`~earwax.Config.from_path`.
        """
        self = cls(**data)  # type: ignore[call-arg]
        a: Attribute
        for a in cls.__attrs_attrs__:  # type: ignore[attr-defined]
            if a.type is not None and isclass(a.type) and issubclass(
                a.type, Config
            ):
                setattr(
                    self, a.name, a.type.from_dict(data[a.name])
                )
        return self
