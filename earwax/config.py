"""Provides the Config class."""

from typing import Any, Dict, Optional

from attr import attrs

DumpDict = Dict[str, Any]


@attrs(auto_attribs=True)
class ConfigValue:
    """A configuration value.

    This class is used to make configuration values::

        class GameConfig(Config):
            name = ConfigValue('username', name='The name of your character')

    :ivar `~earwax.ConfigValue.value`: The value held by this configuration
        value.

    :ivar `~earwax.ConfigValue.name`: The human-readable name of this
        configuration value.

        The name is currently only used by :class:`earwax.ConfigMenu`.

    :ivar `~earwax.ConfigValue.type_`: The type of this value. Can be inferred
        from :attr:`~earwax.ConfigValue.value`.

        Currently this attribute is used by :class:`earwax.ConfigMenu` to
        figure out how to construct the widget that will represent this value.
    """

    value: Any
    name: Optional[str] = None
    type_: Optional[object] = None

    def __attrs_post_init__(self) -> None:
        if self.type_ is None:
            self.type_ = type(self.value)


class Config:
    """Holds configuration subsections and values.

    Any attribute that is an instance of :class:`~earwax.Config` is considered
    a subsection.

    Any attribute that is an instance of :class:`~earwax.ConfigValue` is
    considered a configuration value.
    """

    __config_values__: Dict[str, ConfigValue]
    __config_subsections__: Dict[str, 'Config']

    def __init__(self) -> None:
        """Iterate over the attributes of this class, and add configuration
        values to __config_values__."""
        self.__config_values__ = {}
        self.__config_subsections__ = {}
        cls = type(self)
        name: str
        for name in dir(cls):
            value: Any = getattr(cls, name)
            if isinstance(value, ConfigValue):
                self.__config_values__[name] = value
                setattr(self, name, value.value)
                self.__annotations__[name] = value.type_
            elif isinstance(value, Config):
                self.__config_subsections__[name] = value

    def dump(self) -> DumpDict:
        """Return this object as a dictionary."""
        d: DumpDict = {}
        name: str
        for name in self.__config_values__:
            d[name] = getattr(self, name)
        subsection: Config
        for name, subsection in self.__config_subsections__.items():
            d[name] = subsection.dump()
        return d

    def populate_from_dict(self, data: DumpDict) -> None:
        """Load and return an instance from a dictionary, probably provided by
        :meth:`~earwax.Config.dump`::

            c = Config()
            with open('config.json', 'r') as f:
                c.populate_from_dict(json.load(f))

        As a shortcut, you can use :meth:`~earwax.Config.from_path` to loadfrom
        a file.

        """
        name: str
        value: ConfigValue
        for name, value in self.__config_values__.items():
            setattr(self, name, data.get(name, value.value))
        subsection: Config
        for name, subsection in self.__config_subsections__.items():
            subsection.populate_from_dict(data.get(name, {}))
