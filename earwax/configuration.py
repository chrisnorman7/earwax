"""Provides the Config class."""

from pathlib import Path
from typing import Optional

from .config import Config, ConfigValue


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

    __section_name__ = 'Menus'
    default_item_select_sound: ConfigValue[Optional[Path]] = ConfigValue(
        None, type_=Optional[Path],
        name='The default sound that plays when moving through menus',
        value_converters={
            type(None): lambda o: '<Unset>'
        }
    )
    default_item_select_sound.dump(dump_path)
    default_item_select_sound.load(load_path)

    default_item_activate_sound: ConfigValue[Optional[Path]] = ConfigValue(
        None, type_=Optional[Path],
        name='The default sound that plays when activating items in menus',
        value_converters={
            type(None): lambda o: '<Unset>'
        }
    )
    default_item_activate_sound.dump(dump_path)
    default_item_activate_sound.load(load_path)


class SpeechConfig(Config):
    """The speech configuration section."""

    __section_name__ = 'Speech and Braille'
    speak: ConfigValue = ConfigValue(True, name='Speech')
    braille: ConfigValue = ConfigValue(True, name='Braille')


class SoundConfig(Config):
    """Configure various aspects of the sound system.

    The only thing this is used for internally is the volume of
    :attr:`earwax.Game.interface_sound_player`.
    """

    __section_name__ = 'Sound'
    sound_volume: ConfigValue = ConfigValue(0.5, name='Sound volume')
    music_volume: ConfigValue = ConfigValue(0.4, name='Music volume')
    ambiance_volume: ConfigValue = ConfigValue(0.4, name='Ambiance volume')
    default_cache_size: ConfigValue[int] = ConfigValue(
        1024 ** 2 * 500, name='The size of the default sound cache in bytes'
    )


class EditorConfig(Config):
    """Configure various things about editors."""

    __section_name__ = 'Editors'
    hat_alphabet: ConfigValue = ConfigValue(
        ' abcdefghijklmnopqrstuvwxyz.,1234567890@ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        '-#[]{}', name='Hat alphabet'
    )


class EarwaxConfig(Config):
    """The main earwax configuration.

    You can configure this in your programs, and the main
    :meth:`earwax <earwax.cmd.main.main>` method will use it when
    configuring games made with it.
    """

    __section_name__ = 'Earwax Configuration'
    menus: MenuConfig = MenuConfig()
    speech: SpeechConfig = SpeechConfig()
    sound: SoundConfig = SoundConfig()
    editors: EditorConfig = EditorConfig()
