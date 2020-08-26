"""Provides the Config class."""

from pathlib import Path
from typing import Optional

from .config import Config, ConfigValue


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
    default_item_activate_sounddefault_item_select_sound: ConfigValue = ConfigValue(
        None, type_=Optional[Path],
        name='The default sound that plays when activating items in menus',
        value_converters={
            type(None): lambda o: '<Unset>'
        }
    )


class EarwaxConfig(Config):
    """The main earwax configuration.

    You can configure this in your programs, and the main
    :meth:`earwax <earwax.cmd.main.main>` method will use it when configuring
    games made with it.
    """

    __section_name__ = 'Earwax Configuration'
    menus: MenuConfig = MenuConfig()
