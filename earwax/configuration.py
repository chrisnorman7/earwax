"""Provides the Config class."""

from pathlib import Path
from typing import Optional

from .config import Config, ConfigValue

try:
    ConfigValue('Test')
except TypeError:
    _configValue = ConfigValue

    def ConfigValue(*args, **kwargs) -> _configValue:  # type: ignore[no-redef]
        """This code stops building docs on readthedocs from failing."""
        return _configValue()  # type: ignore[call-arg]


def dump_path(value: Optional[Path]) -> Optional[str]:
    """Return a path as a string."""
    if value is not None:
        return str(value)
    return None


def load_path(value: Optional[str]) -> Optional[Path]:
    """Load a path from a string."""
    if value is not None:
        return Path(value)
    return None


class MenuConfig(Config):
    """The menu configuration section."""

    __section_name__ = 'Menu Configuration'
    default_item_select_sound: ConfigValue = ConfigValue(
        None, type_=Optional[Path],
        name='The default sound that plays when moving through menus',
        value_converters={
            type(None): lambda o: '<Unset>'
        }
    )
    default_item_select_sound.dump(dump_path)
    default_item_select_sound.load(load_path)

    default_item_activate_sound: ConfigValue = ConfigValue(
        None, type_=Optional[Path],
        name='The default sound that plays when activating items in menus',
        value_converters={
            type(None): lambda o: '<Unset>'
        }
    )
    default_item_activate_sound.dump(dump_path)
    default_item_activate_sound.load(load_path)


try:
    class EarwaxConfig(Config):
        """The main earwax configuration.

        You can configure this in your programs, and the main
        :meth:`earwax <earwax.cmd.main.main>` method will use it when
        configuring games made with it.
        """

        __section_name__ = 'Earwax Configuration'
        menus: MenuConfig = MenuConfig()
except TypeError:
    class EarwaxConfig:  # type: ignore[no-redef]
        """This class is used when docs are building."""
        pass
