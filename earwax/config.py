"""Provides the Config and ConfigValue classes."""

from typing import Any, Callable, Dict, Optional, TextIO

from attr import Factory, attrib, attrs
from yaml import FullLoader, dump, load

DumpDict = Dict[str, Any]

DumpLoad = Callable[[Any], Any]


@attrs(auto_attribs=True)
class ConfigValue:
    """A configuration value.

    This class is used to make configuration values::

        name = ConfigValue('username', name='Your character name', type_=str)

    If you are dealing with a non-standard object, you can set custom functions
    for loading and dumping the objects::

        from pathlib import Path
        option = ConfigValue(Path.cwd(), name='Some directory')

        @option.dump
        def dump_path(value: Path) -> str:
            return str(value)

        @option.load
        def load_path(value: str) -> Path:
            return Path(value)

    :ivar `~earwax.ConfigValue.value`: The value held by this configuration
        value.

    :ivar `~earwax.ConfigValue.name`: The human-readable name of this
        configuration value.

        The name is currently only used by :class:`earwax.ConfigMenu`.

    :ivar `~earwax.ConfigValue.type_`: The type of this value. Can be inferred
        from :attr:`~earwax.ConfigValue.value`.

        Currently this attribute is used by :class:`earwax.ConfigMenu` to
        figure out how to construct the widget that will represent this value.

    :ivar ~earwax.ConfigValue.value_converters: A dictionary of ``type``:
        ``converter`` functions.

        These are used by :meth:`earwax.ConfigMenu.option_menu` to print
        :attr:`~earwax.ConfigValue.value`, instead of
        :meth:`~earwax.ConfigValue.value_to_string`.

    :ivar `~earwax.ConfigValue.default`: The default value for this
        configuration value.

        This will be inferred from :attr:`~earwax.ConfigValue.value`.

    :ivar ~earwax.ConfigValue.dump_func: A function that will take the actual
        value, and return something that YAML can dump.

    :ivar ~earwax.ConfigValue.load_func: A function that takes the value that
        was loaded by YAML, and returns the actual value.
    """

    value: Any
    name: Optional[str] = None
    type_: Optional[object] = None
    value_converters: Optional[
        Dict[object, Callable[['ConfigValue'], str]]
    ] = None
    default: Optional[Any] = attrib(default=Factory(type(None)), init=False)
    dump_func: Optional[DumpLoad] = None
    load_func: Optional[DumpLoad] = None

    def __attrs_post_init__(self) -> None:
        if self.type_ is None:
            self.type_ = type(self.value)
        self.default = self.value

    def value_to_string(self) -> str:
        """Return :attr:`~earwax.ConfigValue.value` as a string.

        This method is used by :class:`earwax.ConfigMenu` when it shows
        values."""
        return str(self.value)

    def dump(self, func: DumpLoad) -> DumpLoad:
        """A decorator to add a dump function.

        :param func: The function that should be used.

            See the description for :attr:`~earwax.ConfigValue.dump_func`.
        """
        self.dump_func = func
        return func

    def load(self, func: DumpLoad) -> DumpLoad:
        """A decorator to add a load function.

        :param func: The function to be used.

            See the description for :attr:`~earwax.ConfigValue.load_func`.
        """
        self.load_func = func
        return func


class Config:
    """Holds configuration subsections and values.

    Any attribute that is an instance of :class:`earwax.Config` is considered
    a subsection.

    Any attribute that is an instance of :class:`earwax.ConfigValue` is
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

    To set the name that will be used by :class:`earwax.ConfigMenu`,
    subclass :class:`earwax.Config`, and include a `__section_name__`
    attribute::

        class NamedConfig(Config):
            __section_name__ = 'Options'

    :ivar ~earwax.Config.__section_name__: The human-readable name of this
        section.

        At present, this attribute is only used by :class:`earwax.ConfigMenu`.
    """

    __section_name__: Optional[str] = None
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
            with open('config.yaml', 'w') as f:
                json.dump(d, f)

        Use the :meth:`~earwax.Config.populate_from_dict` method to
        restore dumped values.
        """
        d: DumpDict = {}
        name: str
        option: ConfigValue
        for name, option in self.__config_values__.items():
            value: Any = option.value
            if option.dump_func is not None:
                value = option.dump_func(value)
            d[name] = value
        subsection: Config
        for name, subsection in self.__config_subsections__.items():
            d[name] = subsection.dump()
        return d

    def populate_from_dict(self, data: DumpDict) -> None:
        """Populate values from a dictionary, probably provided by
        :meth:`~earwax.Config.dump`::

            c = Config()
            with open('config.yaml', 'r') as f:
                c.populate_from_dict(json.load(f))

        Any missing values from `data` are ignored.

        :param data: The data to load.
        """
        name: str
        option: ConfigValue
        for name, option in self.__config_values__.items():
            value: Any = data.get(name, option.value)
            if option.load_func is not None:
                value = option.load_func(value)
            option.value = value
        subsection: Config
        for name, subsection in self.__config_subsections__.items():
            subsection.populate_from_dict(data.get(name, {}))

    def save(self, f: TextIO) -> None:
        """Dump this configuration section to a file.

        Uses the :meth:`~earwax.Config.dump` method to get the dumpable data.

        You can save a configuration section like so::

            c = ImaginaryConfigSection()
            with open('config.yaml', 'w') as f:
                c.save(f)

        By default, YAML is used.

        :param f: A file-like object to write the resulting data to.
        """
        data: DumpDict = self.dump()
        dump(data, stream=f)

    def load(self, f: TextIO) -> None:
        """Uses the :meth:`~earwax.Config.populate_from_dict` method on
        dataloaded from the given file::

            c = ImaginaryConfigSection()
            with open('config.yaml', 'r'):
                c.load(f)

        To save the data in the furst place, use the
        :meth:`~earwax.Config.save` method.

        :param f: A file-like object to load data from.
        """
        data: Any = load(f, Loader=FullLoader)
        self.populate_from_dict(data)
