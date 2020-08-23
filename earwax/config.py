"""Provides the Config and ConfigValue classes."""

from typing import Any, Dict, Optional

from attr import Factory, attrs, attrib

DumpDict = Dict[str, Any]


@attrs(auto_attribs=True)
class ConfigValue:
    """A configuration value.

    This class is used to make configuration values::

        name = ConfigValue('username', name='Your character name', type_=str)

    :ivar `~earwax.ConfigValue.value`: The value held by this configuration
        value.

    :ivar `~earwax.ConfigValue.name`: The human-readable name of this
        configuration value.

        The name is currently only used by :class:`earwax.ConfigMenu`.

    :ivar `~earwax.ConfigValue.type_`: The type of this value. Can be inferred
        from :attr:`~earwax.ConfigValue.value`.

        Currently this attribute is used by :class:`earwax.ConfigMenu` to
        figure out how to construct the widget that will represent this value.

    :ivar `~earwax.ConfigValue.default`: The default value for this
        configuration value.

        This will be inferred from :attr:`~earwax.ConfigValue.value`.
    """

    value: Any
    name: Optional[str] = None
    type_: Optional[object] = None
    default: Optional[Any] = attrib(default=Factory(type(None)), init=False)

    def __attrs_post_init__(self) -> None:
        if self.type_ is None:
            self.type_ = type(self.value)
        self.default = self.value


class Config:
    """Holds configuration subsections and values.

    Any attribute that is an instance of :class:`~earwax.Config` is considered
    a subsection.

    Any attribute that is an instance of :class:`~earwax.ConfigValue` is
    considered a configuration value.

    You can create sections like so::

        from earwax import Config, ConfigValue

        class GameConfig(Config):
            '''Example configuration page.'''

            hostname = ConfigValue('localhost')
            port = ConfigValue(1234)

        c = GameConfig()

    Then you can access configuration values like this::

        host_string = f'{c.hostname.value}:{c.port.value}'
        # ...

    Use the :meth:`~earwax.Config.dump` method to get a dictionary suitable for
    dumping with json.
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
            elif isinstance(value, Config):
                self.__config_subsections__[name] = value

    def dump(self) -> DumpDict:
        """Return all configuration values, recursing through subsections::

            c = ImaginaryConfiguration()
            d = c.dump()
            with open('config.json', 'w') as f:
                json.dump(d, f)

        Use the :meth:`~earwax.Config.populate_from_dict` method to
        restore dumped values.
        """
        d: DumpDict = {}
        name: str
        value: ConfigValue
        for name, value in self.__config_values__.items():
            d[name] = value.value
        subsection: Config
        for name, subsection in self.__config_subsections__.items():
            d[name] = subsection.dump()
        return d

    def populate_from_dict(self, data: DumpDict) -> None:
        """Populate values from a dictionary, probably provided by
        :meth:`~earwax.Config.dump`::

            c = Config()
            with open('config.json', 'r') as f:
                c.populate_from_dict(json.load(f))

        Any missing values from `data` are ignored.

        """
        name: str
        value: ConfigValue
        for name, value in self.__config_values__.items():
            value.value = data.get(name, value.value)
        subsection: Config
        for name, subsection in self.__config_subsections__.items():
            subsection.populate_from_dict(data.get(name, {}))
